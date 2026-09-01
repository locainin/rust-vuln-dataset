    fn dispatch(&mut self) -> ReturnCode {
        'label: loop {
            match self.mode {
                Mode::Head => {
                    if self.wrap == 0 {
                        self.mode = Mode::TypeDo;

                        continue 'label;
                    }

                    need_bits!(self, 16);

                    // Gzip
                    if (self.wrap & 2) != 0 && self.bit_reader.hold() == 0x8b1f {
                        if self.wbits == 0 {
                            self.wbits = 15;
                        }

                        let b0 = self.bit_reader.bits(8) as u8;
                        let b1 = (self.bit_reader.hold() >> 8) as u8;
                        self.checksum = crc32(crate::CRC32_INITIAL_VALUE, &[b0, b1]);
                        self.bit_reader.init_bits();

                        self.mode = Mode::Flags;

                        continue 'label;
                    }

                    if let Some(header) = &mut self.head {
                        header.done = -1;
                    }

                    // check if zlib header is allowed
                    if (self.wrap & 1) == 0
                        || ((self.bit_reader.bits(8) << 8) + (self.bit_reader.hold() >> 8)) % 31
                            != 0
                    {
                        self.mode = Mode::Bad;
                        return self.bad("incorrect header check\0");
                    }

                    if self.bit_reader.bits(4) != Z_DEFLATED as u64 {
                        self.mode = Mode::Bad;
                        return self.bad("unknown compression method\0");
                    }

                    self.bit_reader.drop_bits(4);
                    let len = self.bit_reader.bits(4) as u8 + 8;

                    if self.wbits == 0 {
                        self.wbits = len;
                    }

                    if len as i32 > MAX_WBITS || len > self.wbits {
                        self.mode = Mode::Bad;
                        return self.bad("invalid window size\0");
                    }

                    self.dmax = 1 << len;
                    self.gzip_flags = 0; // indicate zlib header
                    self.checksum = crate::ADLER32_INITIAL_VALUE as _;

                    if self.bit_reader.hold() & 0x200 != 0 {
                        self.bit_reader.init_bits();

                        self.mode = Mode::DictId;

                        continue 'label;
                    } else {
                        self.bit_reader.init_bits();

                        self.mode = Mode::Type;

                        continue 'label;
                    }
                }
                Mode::Flags => {
                    need_bits!(self, 16);
                    self.gzip_flags = self.bit_reader.hold() as i32;

                    // Z_DEFLATED = 8 is the only supported method
                    if self.gzip_flags & 0xff != Z_DEFLATED {
                        self.mode = Mode::Bad;
                        return self.bad("unknown compression method\0");
                    }

                    if self.gzip_flags & 0xe000 != 0 {
                        self.mode = Mode::Bad;
                        return self.bad("unknown header flags set\0");
                    }

                    if let Some(head) = self.head.as_mut() {
                        head.text = ((self.bit_reader.hold() >> 8) & 1) as i32;
                    }

                    if (self.gzip_flags & 0x0200) != 0 && (self.wrap & 4) != 0 {
                        let b0 = self.bit_reader.bits(8) as u8;
                        let b1 = (self.bit_reader.hold() >> 8) as u8;
                        self.checksum = crc32(self.checksum, &[b0, b1]);
                    }

                    self.bit_reader.init_bits();
                    self.mode = Mode::Time;

                    continue 'label;
                }
                Mode::Time => {
                    need_bits!(self, 32);
                    if let Some(head) = self.head.as_mut() {
                        head.time = self.bit_reader.hold() as z_size;
                    }

                    if (self.gzip_flags & 0x0200) != 0 && (self.wrap & 4) != 0 {
                        let bytes = (self.bit_reader.hold() as u32).to_le_bytes();
                        self.checksum = crc32(self.checksum, &bytes);
                    }

                    self.bit_reader.init_bits();
                    self.mode = Mode::Os;

                    continue 'label;
                }
                Mode::Os => {
                    need_bits!(self, 16);
                    if let Some(head) = self.head.as_mut() {
                        head.xflags = (self.bit_reader.hold() & 0xff) as i32;
                        head.os = (self.bit_reader.hold() >> 8) as i32;
                    }

                    if (self.gzip_flags & 0x0200) != 0 && (self.wrap & 4) != 0 {
                        let bytes = (self.bit_reader.hold() as u16).to_le_bytes();
                        self.checksum = crc32(self.checksum, &bytes);
                    }

                    self.bit_reader.init_bits();
                    self.mode = Mode::ExLen;

                    continue 'label;
                }
                Mode::ExLen => {
                    if (self.gzip_flags & 0x0400) != 0 {
                        need_bits!(self, 16);

                        // self.length (and head.extra_len) represent the length of the extra field
                        self.length = self.bit_reader.hold() as usize;
                        if let Some(head) = self.head.as_mut() {
                            head.extra_len = self.length as u32;
                        }

                        if (self.gzip_flags & 0x0200) != 0 && (self.wrap & 4) != 0 {
                            let bytes = (self.bit_reader.hold() as u16).to_le_bytes();
                            self.checksum = crc32(self.checksum, &bytes);
                        }
                        self.bit_reader.init_bits();
                    } else if let Some(head) = self.head.as_mut() {
                        head.extra = core::ptr::null_mut();
                    }

                    self.mode = Mode::Extra;

                    continue 'label;
                }
                Mode::Extra => {
                    if (self.gzip_flags & 0x0400) != 0 {
                        // self.length is the number of remaining `extra` bytes. But they may not all be available
                        let extra_available =
                            Ord::min(self.length, self.bit_reader.bytes_remaining());

                        if extra_available > 0 {
                            if let Some(head) = self.head.as_mut() {
                                if !head.extra.is_null() {
                                    // at `head.extra`, the caller has reserved `head.extra_max` bytes.
                                    // in the deflated byte stream, we've found a gzip header with
                                    // `head.extra_len` bytes of data. We must be careful because
                                    // `head.extra_len` may be larger than `head.extra_max`.

                                    // how many bytes we've already written into `head.extra`
                                    let written_so_far = head.extra_len as usize - self.length;

                                    // min of number of bytes available at dst and at src
                                    let count = Ord::min(
                                        (head.extra_max as usize).saturating_sub(written_so_far),
                                        extra_available,
                                    );

                                    // location where we'll write: this saturates at the
                                    // `head.extra.add(head.extra.max)` to prevent UB
                                    let next_write_offset =
                                        Ord::min(written_so_far, head.extra_max as usize);

                                    unsafe {
                                        core::ptr::copy_nonoverlapping(
                                            self.bit_reader.as_mut_ptr(),
                                            head.extra.add(next_write_offset),
                                            count,
                                        );
                                    }
                                }
                            }

                            // Checksum
                            if (self.gzip_flags & 0x0200) != 0 && (self.wrap & 4) != 0 {
                                let extra_slice = &self.bit_reader.as_slice()[..extra_available];
                                self.checksum = crc32(self.checksum, extra_slice)
                            }

                            self.in_available -= extra_available;
                            self.bit_reader.advance(extra_available);
                            self.length -= extra_available;
                        }

                        // Checks for errors occur after returning
                        if self.length != 0 {
                            return self.inflate_leave(ReturnCode::Ok);
                        }
                    }

                    self.length = 0;
                    self.mode = Mode::Name;

                    continue 'label;
                }
                Mode::Name => {
                    if (self.gzip_flags & 0x0800) != 0 {
                        if self.in_available == 0 {
                            return self.inflate_leave(ReturnCode::Ok);
                        }

                        // the name string will always be null-terminated, but might be longer than we have
                        // space for in the header struct. Nonetheless, we read the whole thing.
                        let slice = self.bit_reader.as_slice();
                        let null_terminator_index = slice.iter().position(|c| *c == 0);

                        // we include the null terminator if it exists
                        let name_slice = match null_terminator_index {
                            Some(i) => &slice[..=i],
                            None => slice,
                        };

                        // if the header has space, store as much as possible in there
                        if let Some(head) = self.head.as_mut() {
                            if !head.name.is_null() {
                                let remaining_name_bytes =
                                    (head.name_max as usize).saturating_sub(self.length);
                                let copy = Ord::min(name_slice.len(), remaining_name_bytes);

                                unsafe {
                                    core::ptr::copy_nonoverlapping(
                                        name_slice.as_ptr(),
                                        head.name.add(self.length),
                                        copy,
                                    )
                                };

                                self.length += copy;
                            }
                        }

                        if (self.gzip_flags & 0x0200) != 0 && (self.wrap & 4) != 0 {
                            self.checksum = crc32(self.checksum, name_slice);
                        }

                        let reached_end = name_slice.last() == Some(&0);
                        self.bit_reader.advance(name_slice.len());

                        if !reached_end && self.bit_reader.bytes_remaining() == 0 {
                            return self.inflate_leave(ReturnCode::Ok);
                        }
                    } else if let Some(head) = self.head.as_mut() {
                        head.name = core::ptr::null_mut();
                    }

                    self.length = 0;
                    self.mode = Mode::Comment;

                    continue 'label;
                }
                Mode::Comment => {
                    if (self.gzip_flags & 0x01000) != 0 {
                        if self.in_available == 0 {
                            return self.inflate_leave(ReturnCode::Ok);
                        }

                        // the comment string will always be null-terminated, but might be longer than we have
                        // space for in the header struct. Nonetheless, we read the whole thing.
                        let slice = self.bit_reader.as_slice();
                        let null_terminator_index = slice.iter().position(|c| *c == 0);

                        // we include the null terminator if it exists
                        let comment_slice = match null_terminator_index {
                            Some(i) => &slice[..=i],
                            None => slice,
                        };

                        // if the header has space, store as much as possible in there
                        if let Some(head) = self.head.as_mut() {
                            if !head.comment.is_null() {
                                let remaining_comm_bytes =
                                    (head.comm_max as usize).saturating_sub(self.length);
                                let copy = Ord::min(comment_slice.len(), remaining_comm_bytes);
                                unsafe {
                                    core::ptr::copy_nonoverlapping(
                                        comment_slice.as_ptr(),
                                        head.comment.add(self.length),
                                        copy,
                                    )
                                };

                                self.length += copy;
                            }
                        }

                        if (self.gzip_flags & 0x0200) != 0 && (self.wrap & 4) != 0 {
                            self.checksum = crc32(self.checksum, comment_slice);
                        }

                        let reached_end = comment_slice.last() == Some(&0);
                        self.bit_reader.advance(comment_slice.len());

                        if !reached_end && self.bit_reader.bytes_remaining() == 0 {
                            return self.inflate_leave(ReturnCode::Ok);
                        }
                    } else if let Some(head) = self.head.as_mut() {
                        head.comment = core::ptr::null_mut();
                    }

                    self.mode = Mode::HCrc;

                    continue 'label;
                }
                Mode::HCrc => {
                    if (self.gzip_flags & 0x0200) != 0 {
                        need_bits!(self, 16);

                        if (self.wrap & 4) != 0
                            && self.bit_reader.hold() as u32 != (self.checksum & 0xffff)
                        {
                            self.mode = Mode::Bad;
                            return self.bad("header crc mismatch\0");
                        }

                        self.bit_reader.init_bits();
                    }

                    if let Some(head) = self.head.as_mut() {
                        head.hcrc = (self.gzip_flags >> 9) & 1;
                        head.done = 1;
                    }

                    // compute crc32 checksum if not in raw mode
                    if (self.wrap & 4 != 0) && self.gzip_flags != 0 {
                        self.crc_fold = Crc32Fold::new();
                        self.checksum = crate::CRC32_INITIAL_VALUE;
                    }

                    self.mode = Mode::Type;

                    continue 'label;
                }
                Mode::Type => {
                    use InflateFlush::*;

                    match self.flush {
                        Block | Trees => return ReturnCode::Ok,
                        NoFlush | SyncFlush | Finish => {
                            // NOTE: this is slightly different to what zlib-rs does!
                            self.mode = Mode::TypeDo;
                            continue 'label;
                        }
                    }
                }
                Mode::TypeDo => {
                    if self.flags.contains(Flags::IS_LAST_BLOCK) {
                        self.bit_reader.next_byte_boundary();
                        self.mode = Mode::Check;

                        continue 'label;
                    }

                    need_bits!(self, 3);
                    // self.last = self.bit_reader.bits(1) != 0;
                    self.flags
                        .update(Flags::IS_LAST_BLOCK, self.bit_reader.bits(1) != 0);
                    self.bit_reader.drop_bits(1);

                    match self.bit_reader.bits(2) {
                        0 => {
                            // eprintln!("inflate:     stored block (last = {last})");

                            self.bit_reader.drop_bits(2);

                            self.mode = Mode::Stored;

                            continue 'label;
                        }
                        1 => {
                            // eprintln!("inflate:     fixed codes block (last = {last})");

                            self.len_table = Table {
                                codes: Codes::Fixed,
                                bits: 9,
                            };

                            self.dist_table = Table {
                                codes: Codes::Fixed,
                                bits: 5,
                            };

                            self.mode = Mode::Len_;

                            self.bit_reader.drop_bits(2);

                            if let InflateFlush::Trees = self.flush {
                                return self.inflate_leave(ReturnCode::Ok);
                            } else {
                                continue 'label;
                            }
                        }
                        2 => {
                            // eprintln!("inflate:     dynamic codes block (last = {last})");

                            self.bit_reader.drop_bits(2);

                            self.mode = Mode::Table;

                            continue 'label;
                        }
                        3 => {
                            // eprintln!("inflate:     invalid block type");

                            self.bit_reader.drop_bits(2);

                            self.mode = Mode::Bad;
                            return self.bad("invalid block type\0");
                        }
                        _ => unsafe { core::hint::unreachable_unchecked() },
                    }
                }
                Mode::Stored => {
                    self.bit_reader.next_byte_boundary();

                    need_bits!(self, 32);

                    let hold = self.bit_reader.bits(32) as u32;

                    // eprintln!("hold {hold:#x}");

                    if hold as u16 != !((hold >> 16) as u16) {
                        self.mode = Mode::Bad;
                        return self.bad("invalid stored block lengths\0");
                    }

                    self.length = hold as usize & 0xFFFF;
                    // eprintln!("inflate:     stored length {}", state.length);

                    self.bit_reader.init_bits();

                    if let InflateFlush::Trees = self.flush {
                        return self.inflate_leave(ReturnCode::Ok);
                    } else {
                        self.mode = Mode::CopyBlock;

                        continue 'label;
                    }
                }
                Mode::CopyBlock => {
                    loop {
                        let mut copy = self.length;

                        if copy == 0 {
                            break;
                        }

                        copy = Ord::min(copy, self.writer.remaining());
                        copy = Ord::min(copy, self.bit_reader.bytes_remaining());

                        if copy == 0 {
                            return self.inflate_leave(ReturnCode::Ok);
                        }

                        self.writer.extend(&self.bit_reader.as_slice()[..copy]);
                        self.bit_reader.advance(copy);

                        self.length -= copy;
                    }

                    self.mode = Mode::Type;

                    continue 'label;
                }
                Mode::Check => {
                    if !cfg!(feature = "__internal-fuzz-disable-checksum") && self.wrap != 0 {
                        need_bits!(self, 32);

                        self.total += self.writer.len();

                        if self.wrap & 4 != 0 {
                            if self.gzip_flags != 0 {
                                self.crc_fold.fold(self.writer.filled(), self.checksum);
                                self.checksum = self.crc_fold.finish();
                            } else {
                                self.checksum = adler32(self.checksum, self.writer.filled());
                            }
                        }

                        let given_checksum = if self.gzip_flags != 0 {
                            self.bit_reader.hold() as u32
                        } else {
                            zswap32(self.bit_reader.hold() as u32)
                        };

                        self.out_available = self.writer.capacity() - self.writer.len();

                        if self.wrap & 4 != 0 && given_checksum != self.checksum {
                            self.mode = Mode::Bad;
                            return self.bad("incorrect data check\0");
                        }

                        self.bit_reader.init_bits();
                    }
                    self.mode = Mode::Length;

                    continue 'label;
                }
                Mode::Len => {
                    let avail_in = self.bit_reader.bytes_remaining();
                    let avail_out = self.writer.remaining();

                    // INFLATE_FAST_MIN_LEFT is important. It makes sure there is at least 32 bytes of free
                    // space available. This means for many SIMD operations we don't need to process a
                    // remainder; we just copy blindly, and a later operation will overwrite the extra copied
                    // bytes
                    if avail_in >= INFLATE_FAST_MIN_HAVE && avail_out >= INFLATE_FAST_MIN_LEFT {
                        inflate_fast_help(self, 0);
                        continue 'label;
                    }

                    self.back = 0;

                    // get a literal, length, or end-of-block code
                    let mut here;
                    loop {
                        let bits = self.bit_reader.bits(self.len_table.bits);
                        here = self.len_table_get(bits as usize);

                        if here.bits <= self.bit_reader.bits_in_buffer() {
                            break;
                        }

                        pull_byte!(self);
                    }

                    if here.op != 0 && here.op & 0xf0 == 0 {
                        let last = here;
                        loop {
                            let bits = self.bit_reader.bits((last.bits + last.op) as usize) as u16;
                            here = self.len_table_get((last.val + (bits >> last.bits)) as usize);
                            if last.bits + here.bits <= self.bit_reader.bits_in_buffer() {
                                break;
                            }

                            pull_byte!(self);
                        }

                        self.bit_reader.drop_bits(last.bits);
                        self.back += last.bits as usize;
                    }

                    self.bit_reader.drop_bits(here.bits);
                    self.back += here.bits as usize;
                    self.length = here.val as usize;

                    if here.op == 0 {
                        self.mode = Mode::Lit;

                        continue 'label;
                    } else if here.op & 32 != 0 {
                        // end of block

                        // eprintln!("inflate:         end of block");

                        self.back = usize::MAX;
                        self.mode = Mode::Type;

                        continue 'label;
                    } else if here.op & 64 != 0 {
                        self.mode = Mode::Bad;

                        return self.bad("invalid literal/length code\0");
                    } else {
                        // length code
                        self.extra = (here.op & MAX_BITS) as usize;
                        self.mode = Mode::LenExt;

                        continue 'label;
                    }
                }
                Mode::Len_ => {
                    self.mode = Mode::Len;

                    continue 'label;
                }
                Mode::LenExt => {
                    let extra = self.extra;

                    // get extra bits, if any
                    if extra != 0 {
                        need_bits!(self, extra);
                        self.length += self.bit_reader.bits(extra) as usize;
                        self.bit_reader.drop_bits(extra as u8);
                        self.back += extra;
                    }

                    // eprintln!("inflate: length {}", state.length);

                    self.was = self.length;
                    self.mode = Mode::Dist;

                    continue 'label;
                }
                Mode::Lit => {
                    if self.writer.is_full() {
                        #[cfg(all(test, feature = "std"))]
                        eprintln!("Ok: writer is full ({} bytes)", self.writer.capacity());
                        return self.inflate_leave(ReturnCode::Ok);
                    }

                    self.writer.push(self.length as u8);

                    self.mode = Mode::Len;

                    continue 'label;
                }
                Mode::Dist => {
                    // get distance code
                    let mut here;
                    loop {
                        let bits = self.bit_reader.bits(self.dist_table.bits) as usize;
                        here = self.dist_table_get(bits);
                        if here.bits <= self.bit_reader.bits_in_buffer() {
                            break;
                        }

                        pull_byte!(self);
                    }

                    if here.op & 0xf0 == 0 {
                        let last = here;

                        loop {
                            let bits = self.bit_reader.bits((last.bits + last.op) as usize);
                            here = self
                                .dist_table_get(last.val as usize + ((bits as usize) >> last.bits));

                            if last.bits + here.bits <= self.bit_reader.bits_in_buffer() {
                                break;
                            }

                            pull_byte!(self);
                        }

                        self.bit_reader.drop_bits(last.bits);
                        self.back += last.bits as usize;
                    }

                    self.bit_reader.drop_bits(here.bits);

                    if here.op & 64 != 0 {
                        self.mode = Mode::Bad;
                        return self.bad("invalid distance code\0");
                    }

                    self.offset = here.val as usize;

                    self.extra = (here.op & MAX_BITS) as usize;
                    self.mode = Mode::DistExt;

                    continue 'label;
                }
                Mode::DistExt => {
                    let extra = self.extra;

                    if extra > 0 {
                        need_bits!(self, extra);
                        self.offset += self.bit_reader.bits(extra) as usize;
                        self.bit_reader.drop_bits(extra as u8);
                        self.back += extra;
                    }

                    if INFLATE_STRICT && self.offset > self.dmax {
                        self.mode = Mode::Bad;
                        return self.bad("invalid distance code too far back\0");
                    }

                    // eprintln!("inflate: distance {}", state.offset);

                    self.mode = Mode::Match;

                    continue 'label;
                }
                Mode::Match => {
                    'match_: loop {
                        if self.writer.is_full() {
                            #[cfg(all(feature = "std", test))]
                            eprintln!(
                                "BufError: writer is full ({} bytes)",
                                self.writer.capacity()
                            );
                            return self.inflate_leave(ReturnCode::Ok);
                        }

                        let left = self.writer.remaining();
                        let copy = self.writer.len();

                        let copy = if self.offset > copy {
                            // copy from window to output

                            let mut copy = self.offset - copy;

                            if copy > self.window.have() {
                                if self.flags.contains(Flags::SANE) {
                                    self.mode = Mode::Bad;
                                    return self.bad("invalid distance too far back\0");
                                }

                                // TODO INFLATE_ALLOW_INVALID_DISTANCE_TOOFAR_ARRR
                                panic!("INFLATE_ALLOW_INVALID_DISTANCE_TOOFAR_ARRR")
                            }

                            let wnext = self.window.next();
                            let wsize = self.window.size();

                            let from = if copy > wnext {
                                copy -= wnext;
                                wsize - copy
                            } else {
                                wnext - copy
                            };

                            copy = Ord::min(copy, self.length);
                            copy = Ord::min(copy, left);

                            self.writer
                                .extend_from_window(&self.window, from..from + copy);

                            copy
                        } else {
                            let copy = Ord::min(self.length, left);
                            self.writer.copy_match(self.offset, copy);

                            copy
                        };

                        self.length -= copy;

                        if self.length == 0 {
                            self.mode = Mode::Len;

                            continue 'label;
                        } else {
                            // otherwise it seems to recurse?
                            continue 'match_;
                        }
                    }
                }
                Mode::Done => todo!(),
                Mode::Table => {
                    need_bits!(self, 14);
                    self.nlen = self.bit_reader.bits(5) as usize + 257;
                    self.bit_reader.drop_bits(5);
                    self.ndist = self.bit_reader.bits(5) as usize + 1;
                    self.bit_reader.drop_bits(5);
                    self.ncode = self.bit_reader.bits(4) as usize + 4;
                    self.bit_reader.drop_bits(4);

                    // TODO pkzit_bug_workaround
                    if self.nlen > 286 || self.ndist > 30 {
                        self.mode = Mode::Bad;
                        return self.bad("too many length or distance symbols\0");
                    }

                    self.have = 0;
                    self.mode = Mode::LenLens;

                    continue 'label;
                }
                Mode::LenLens => {
                    // permutation of code lengths ;
                    const ORDER: [u16; 19] = [
                        16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15,
                    ];

                    while self.have < self.ncode {
                        need_bits!(self, 3);
                        self.lens[ORDER[self.have] as usize] = self.bit_reader.bits(3) as u16;
                        self.have += 1;
                        self.bit_reader.drop_bits(3);
                    }

                    while self.have < 19 {
                        self.lens[ORDER[self.have] as usize] = 0;
                        self.have += 1;
                    }

                    self.len_table.bits = 7;

                    let InflateTable::Success(root) = inflate_table(
                        CodeType::Codes,
                        &self.lens,
                        19,
                        &mut self.codes_codes,
                        self.len_table.bits,
                        &mut self.work,
                    ) else {
                        self.mode = Mode::Bad;
                        return self.bad("invalid code lengths set\0");
                    };

                    self.len_table.codes = Codes::Codes;
                    self.len_table.bits = root;

                    self.have = 0;
                    self.mode = Mode::CodeLens;

                    continue 'label;
                }
                Mode::CodeLens => {
                    while self.have < self.nlen + self.ndist {
                        let here = loop {
                            let bits = self.bit_reader.bits(self.len_table.bits);
                            let here = self.len_table_get(bits as usize);
                            if here.bits <= self.bit_reader.bits_in_buffer() {
                                break here;
                            }

                            pull_byte!(self);
                        };

                        let here_bits = here.bits;

                        match here.val {
                            0..=15 => {
                                self.bit_reader.drop_bits(here_bits);
                                self.lens[self.have] = here.val;
                                self.have += 1;
                            }
                            16 => {
                                need_bits!(self, here_bits as usize + 2);
                                self.bit_reader.drop_bits(here_bits);
                                if self.have == 0 {
                                    self.mode = Mode::Bad;
                                    return self.bad("invalid bit length repeat\0");
                                }

                                let len = self.lens[self.have - 1];
                                let copy = 3 + self.bit_reader.bits(2) as usize;
                                self.bit_reader.drop_bits(2);

                                if self.have + copy > self.nlen + self.ndist {
                                    self.mode = Mode::Bad;
                                    return self.bad("invalid bit length repeat\0");
                                }

                                for _ in 0..copy {
                                    self.lens[self.have] = len;
                                    self.have += 1;
                                }
                            }
                            17 => {
                                need_bits!(self, here_bits as usize + 3);
                                self.bit_reader.drop_bits(here_bits);
                                let len = 0;
                                let copy = 3 + self.bit_reader.bits(3) as usize;
                                self.bit_reader.drop_bits(3);

                                if self.have + copy > self.nlen + self.ndist {
                                    self.mode = Mode::Bad;
                                    return self.bad("invalid bit length repeat\0");
                                }

                                for _ in 0..copy {
                                    self.lens[self.have] = len as u16;
                                    self.have += 1;
                                }
                            }
                            18.. => {
                                need_bits!(self, here_bits as usize + 7);
                                self.bit_reader.drop_bits(here_bits);
                                let len = 0;
                                let copy = 11 + self.bit_reader.bits(7) as usize;
                                self.bit_reader.drop_bits(7);

                                if self.have + copy > self.nlen + self.ndist {
                                    self.mode = Mode::Bad;
                                    return self.bad("invalid bit length repeat\0");
                                }

                                for _ in 0..copy {
                                    self.lens[self.have] = len as u16;
                                    self.have += 1;
                                }
                            }
                        }
                    }

                    // check for end-of-block code (better have one)
                    if self.lens[256] == 0 {
                        self.mode = Mode::Bad;
                        return self.bad("invalid code -- missing end-of-block\0");
                    }

                    // build code tables

                    self.len_table.bits = 10;

                    let InflateTable::Success(root) = inflate_table(
                        CodeType::Lens,
                        &self.lens,
                        self.nlen,
                        &mut self.len_codes,
                        self.len_table.bits,
                        &mut self.work,
                    ) else {
                        self.mode = Mode::Bad;
                        return self.bad("invalid literal/lengths set\0");
                    };

                    self.len_table.codes = Codes::Len;
                    self.len_table.bits = root;

                    self.dist_table.bits = 9;

                    let InflateTable::Success(root) = inflate_table(
                        CodeType::Dists,
                        &self.lens[self.nlen..],
                        self.ndist,
                        &mut self.dist_codes,
                        self.dist_table.bits,
                        &mut self.work,
                    ) else {
                        self.mode = Mode::Bad;
                        return self.bad("invalid distances set\0");
                    };

                    self.dist_table.bits = root;
                    self.dist_table.codes = Codes::Dist;

                    self.mode = Mode::Len_;

                    if matches!(self.flush, InflateFlush::Trees) {
                        return self.inflate_leave(ReturnCode::Ok);
                    }

                    continue 'label;
                }
                Mode::Dict => {
                    if !self.flags.contains(Flags::HAVE_DICT) {
                        return self.inflate_leave(ReturnCode::NeedDict);
                    }

                    self.checksum = crate::ADLER32_INITIAL_VALUE as _;

                    self.mode = Mode::Type;

                    continue 'label;
                }
                Mode::DictId => {
                    need_bits!(self, 32);

                    self.checksum = zswap32(self.bit_reader.hold() as u32);

                    self.bit_reader.init_bits();

                    self.mode = Mode::Dict;

                    continue 'label;
                }
                Mode::Bad => {
                    let msg = "repeated call with bad state\0";
                    #[cfg(all(feature = "std", test))]
                    dbg!(msg);
                    self.error_message = Some(msg);

                    return ReturnCode::DataError;
                }
                Mode::Mem => {
                    return ReturnCode::MemError;
                }
                Mode::Sync => {
                    return ReturnCode::StreamError;
                }
                Mode::Length => {
                    // for gzip, last bytes contain LENGTH
                    if self.wrap != 0 && self.gzip_flags != 0 {
                        need_bits!(self, 32);
                        if (self.wrap & 4) != 0 && self.bit_reader.hold() != self.total as u64 {
                            self.mode = Mode::Bad;
                            return self.bad("incorrect length check\0");
                        }

                        self.bit_reader.init_bits();
                    }

                    // inflate stream terminated properly
                    return ReturnCode::StreamEnd;
                }
            };
        }
    }
