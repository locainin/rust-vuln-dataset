    fn next(&mut self) -> Option<Self::Item> {
        tracer!(TRACE, "RawCertParser::next", 0);

        // Return the pending error.
        if let Some(err) = self.pending_error.take() {
            t!("Returning the queued error: {}", err);
            return Some(Err(err));
        }

        if self.done {
            return None;
        }

        if self.reader.eof() && self.dearmor {
            // We are dearmoring and hit EOF.  Maybe there is a second
            // armor block next to this one!

            // Get the reader,
            let reader = std::mem::replace(
                &mut self.reader,
                EOF::with_cookie(Default::default()).into_boxed());

            // peel off the armor reader,
            let reader = reader.into_inner().expect("the armor reader");

            // and install a new one!
            self.reader = armor::Reader::from_cookie_reader(
                reader, armor::ReaderMode::Tolerant(None),
                Default::default()).into_boxed();
        }

        if self.reader.eof() {
            return None;
        }

        let mut reader = Dup::with_cookie(
            std::mem::replace(&mut self.reader,
                              Box::new(EOF::with_cookie(Default::default()))),
                Default::default());

        // The absolute start of this certificate in the stream.
        let cert_start_absolute = self.bytes_read;

        // The number of bytes processed relative to the start of the
        // dup'ed buffered reader.  This may be less than the number
        // of bytes read, e.g., when we encounter a new certificate,
        // we read the header, but we don't necessarily want to
        // consider it consumed.
        let mut processed = 0;

        // The certificate's span relative to the start of the dup'ed
        // buffered reader.  The start will be larger than zero when
        // we skip a marker packet.
        let mut cert_start = 0;
        let mut cert_end = 0;

        // (Tag, header length, offset from start of the certificate)
        let mut packets: Vec<(Tag, usize, usize)> = Vec::new();
        let mut primary_key = None;

        let mut pending_error = None;
        'packet_parser: loop {
            if reader.eof() {
                break;
            }

            let packet_start = reader.total_out();
            processed = packet_start;

            let mut skip = 0;
            let mut header_len = 0;
            let header = loop {
                match Header::parse(&mut reader) {
                    Err(err) => {
                        if skip == 0 {
                            t!("Reading the next packet's header: {}", err);
                        }

                        if skip >= RECOVERY_THRESHOLD {
                            pending_error = Some(err.context(
                                format!("Splitting keyring at offset {}",
                                        self.bytes_read + packet_start)));
                            processed = reader.total_out();

                            // We tried to recover and failed.  Once
                            // we return the above error, we're done.
                            self.done = true;

                            break 'packet_parser;
                        } else if reader.eof() {
                            t!("EOF while trying to recover");
                            skip += 1;
                            break Header::new(CTB::new(Tag::Reserved),
                                              BodyLength::Full(skip as u32));
                        } else {
                            skip += 1;
                            reader.rewind();
                            reader.consume(packet_start + skip);
                        }
                    }
                    Ok(header) if skip > 0 => {
                        if PacketParser::plausible_cert(&mut reader, &header)
                            .is_ok()
                        {
                            // We recovered.  First return an error.  The
                            // next time this function is called, we'll
                            // resume here.
                            t!("Found a valid header after {} bytes \
                                of junk: {:?}",
                               skip, header);

                            break Header::new(CTB::new(Tag::Reserved),
                                              BodyLength::Full(skip as u32));
                        } else {
                            skip += 1;
                            reader.rewind();
                            reader.consume(packet_start + skip);
                        }
                    }
                    Ok(header) => {
                        header_len = reader.total_out() - packet_start;
                        break header;
                    }
                }
            };

            if skip > 0 {
                // Fabricate a header.
                t!("Recovered after {} bytes of junk", skip);

                pending_error = Some(crate::Error::MalformedPacket(
                    format!("Encountered {} bytes of junk at offset {}",
                            skip, self.bytes_read)).into());

                // Be careful: if we recovered, then we
                // reader.total_out() includes the good header.
                processed += skip;

                break;
            }

            let tag = header.ctb().tag();
            t!("Found a {:?}, length: {:?}",
               tag, header.length());

            if packet_start > cert_start
                && (tag == Tag::PublicKey || tag == Tag::SecretKey)
            {
                // Start of new cert.  Note: we don't advanced
                // processed!  That would consume the header that
                // we want to read the next time this function is
                // called.
                t!("Stopping: found the start of a new cert ({})", tag);
                break;
            }

            match header.length() {
                BodyLength::Full(l) => {
                    let l = *l as usize;

                    match reader.data_consume_hard(l) {
                        Err(err) => {
                            t!("Stopping: reading {}'s body: {}", tag, err);

                            // If we encountered an EOF while reading
                            // the packet body, then we're done.
                            if err.kind() == std::io::ErrorKind::UnexpectedEof {
                                t!("Got an unexpected EOF, done.");
                                self.done = true;
                            }

                            pending_error = Some(
                                anyhow::Error::from(err).context(format!(
                                    "While reading {}'s body", tag)));

                            break;
                        }
                        Ok(data) => {
                            if tag == Tag::PublicKey
                                || tag == Tag::SecretKey
                            {
                                let data = &data[..l];
                                match Key::from_bytes(data) {
                                    Err(err) => {
                                        t!("Stopping: parsing public key: {}",
                                           err);
                                        pending_error = Some(err);
                                        break;
                                    }
                                    Ok(key) => primary_key = Some(
                                        key.parts_into_public()
                                            .role_into_primary()),
                                }
                            }
                        }
                    }
                }
                BodyLength::Partial(_) => {
                    t!("Stopping: Partial body length not allowed \
                        for {} packets",
                       tag);
                    pending_error = Some(
                        crate::Error::MalformedPacket(
                            format!("Packet {} uses partial body length \
                                     encoding, which is not allowed in \
                                     certificates",
                                    tag))
                            .into());
                    self.done = true;
                    break;
                }
                BodyLength::Indeterminate => {
                    t!("Stopping: Indeterminate length not allowed \
                        for {} packets",
                       tag);
                    pending_error = Some(
                        crate::Error::MalformedPacket(
                            format!("Packet {} uses intedeterminite length \
                                     encoding, which is not allowed in \
                                     certificates",
                                    tag))
                            .into());
                    self.done = true;
                    break;
                }
            }

            let end = reader.total_out();
            processed = end;

            let r = if packet_start == cert_start {
                if tag == Tag::Marker {
                    // Silently skip marker packets at the start of a
                    // packet sequence.
                    cert_start = end;
                    Ok(())
                } else {
                    packets.push((tag, header_len, packet_start));
                    Cert::valid_start(tag)
                }
            } else {
                packets.push((tag, header_len, packet_start));
                Cert::valid_packet(tag)
            };
            if let Err(err) = r {
                t!("Stopping: {:?} => not a certificate: {}", header, err);
                pending_error = Some(err);

                if self.bytes_read == 0 && packet_start == cert_start
                    && matches!(tag, Tag::Unknown(_) | Tag::Private(_))
                {
                    // The very first packet is not known.  Don't
                    // bother to parse anything else.
                    self.done = true;
                }

                break;
            }

            cert_end = end;
        }

        t!("{} bytes processed; RawCert @ offset {}, {} bytes",
           processed,
           self.bytes_read + cert_start, cert_end - cert_start);

        assert!(cert_start <= cert_end);
        assert!(cert_end <= processed);
        self.bytes_read += processed;

        // Strip the buffered_reader::Dup.
        self.reader = Box::new(reader).into_inner()
            .expect("just put it there");

        // Consume the data.
        let cert_data = &self.reader
            .data_consume_hard(processed)
            .expect("just read it")[cert_start..cert_end];

        if let Some(err) = pending_error.take() {
            if cert_start == cert_end {
                // We didn't read anything.
                t!("Directly returning the error");
                return Some(Err(err));
            } else {
                t!("Queuing the error");
                self.pending_error = Some(err);
            }
        }

        if cert_start == cert_end {
            t!("No data.");
            return None;
        }

        Some(Ok(RawCert {
            data: if let Some(slice) = self.slice.as_ref() {
                let data = &slice[cert_start_absolute + cert_start
                                  ..cert_start_absolute + cert_end];
                assert_eq!(data, cert_data);
                Cow::Borrowed(data)
            } else {
                Cow::Owned(cert_data.to_vec())
            },
            primary_key: primary_key.expect("set"),
            packets,
        }))
    }
