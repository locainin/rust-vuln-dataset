    fn data_helper(&mut self, amount: usize, hard: bool, and_consume: bool)
                   -> io::Result<&[u8]> {
        tracer!(TRACE, "Generic::data_helper");
        t!("amount: {}, hard: {}, and_consume: {} (cursor: {}, buffer: {:?})",
           amount, hard, and_consume,
           self.cursor,
           self.buffer.as_ref().map(|buffer| buffer.len()));

        if let Some(ref buffer) = self.buffer {
            // We have a buffer.  Make sure `cursor` is sane.
            assert!(self.cursor <= buffer.len());
        } else {
            // We don't have a buffer.  Make sure cursor is 0.
            assert_eq!(self.cursor, 0);
        }

        let amount_buffered
            = self.buffer.as_ref().map(|b| b.len() - self.cursor).unwrap_or(0);
        if amount > amount_buffered {
            // The caller wants more data than we have readily
            // available.  Read some more.

            let capacity : usize = amount.saturating_add(
                default_buf_size().max(
                    self.preferred_chunk_size.saturating_mul(2)));

            let mut buffer_new = self.unused_buffer.take()
                .map(|mut v| {
                    vec_resize(&mut v, capacity);
                    v
                })
                .unwrap_or_else(|| vec![0u8; capacity]);

            let mut amount_read = 0;
            while amount_buffered + amount_read < amount {
                t!("Have {} bytes, need {} bytes",
                   amount_buffered + amount_read, amount);

                if self.eof {
                    t!("Hit EOF on the underlying reader, don't poll again.");
                    break;
                }

                // See if there is an error from the last invocation.
                if let Some(e) = &self.error {
                    t!("We have a stashed error, don't poll again: {}", e);
                    break;
                }

                match self.reader.read(&mut buffer_new
                                       [amount_buffered + amount_read..]) {
                    Ok(read) => {
                        t!("Read {} bytes", read);
                        if read == 0 {
                            self.eof = true;
                            break;
                        } else {
                            amount_read += read;
                            continue;
                        }
                    },
                    Err(ref err) if err.kind() == ErrorKind::Interrupted =>
                        continue,
                    Err(err) => {
                        // Don't return yet, because we may have
                        // actually read something.
                        self.error = Some(err);
                        break;
                    },
                }
            }

            if amount_read > 0 {
                // We read something.
                if let Some(ref buffer) = self.buffer {
                    // We need to copy in the old data.
                    buffer_new[0..amount_buffered]
                        .copy_from_slice(
                            &buffer[self.cursor..self.cursor + amount_buffered]);
                }

                vec_truncate(&mut buffer_new, amount_buffered + amount_read);

                self.unused_buffer = self.buffer.take();
                self.buffer = Some(buffer_new);
                self.cursor = 0;
            }
        }

        let amount_buffered
            = self.buffer.as_ref().map(|b| b.len() - self.cursor).unwrap_or(0);

        if self.error.is_some() {
            t!("Encountered an error: {}", self.error.as_ref().unwrap());
            // An error occurred.  If we have enough data to fulfill
            // the caller's request, then don't return the error.
            if hard && amount > amount_buffered {
                t!("Not enough data to fulfill request, returning error");
                return Err(self.error.take().unwrap());
            }
            if !hard && amount_buffered == 0 {
                t!("No data data buffered, returning error");
                return Err(self.error.take().unwrap());
            }
        }

        if hard && amount_buffered < amount {
            t!("Unexpected EOF");
            Err(Error::new(ErrorKind::UnexpectedEof, "EOF"))
        } else if amount == 0 || amount_buffered == 0 {
            t!("Returning zero-length slice");
            Ok(&b""[..])
        } else {
            let buffer = self.buffer.as_ref().unwrap();
            if and_consume {
                let amount_consumed = cmp::min(amount_buffered, amount);
                self.cursor += amount_consumed;
                assert!(self.cursor <= buffer.len());
                t!("Consuming {} bytes, returning {} bytes",
                   amount_consumed,
                   buffer[self.cursor-amount_consumed..].len());
                Ok(&buffer[self.cursor-amount_consumed..])
            } else {
                t!("Returning {} bytes",
                   buffer[self.cursor..].len());
                Ok(&buffer[self.cursor..])
            }
        }
    }
