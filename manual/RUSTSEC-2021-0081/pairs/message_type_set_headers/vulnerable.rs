    fn set_headers(
        &mut self,
        slice: &Bytes,
        raw_headers: &[HeaderIndex],
    ) -> Result<PayloadLength, ParseError> {
        let mut ka = None;
        let mut has_upgrade_websocket = false;
        let mut expect = false;
        let mut chunked = false;
        let mut content_length = None;

        {
            let headers = self.headers_mut();

            for idx in raw_headers.iter() {
                let name =
                    HeaderName::from_bytes(&slice[idx.name.0..idx.name.1]).unwrap();

                // SAFETY: httparse already checks header value is only visible ASCII bytes
                // from_maybe_shared_unchecked contains debug assertions so they are omitted here
                let value = unsafe {
                    HeaderValue::from_maybe_shared_unchecked(
                        slice.slice(idx.value.0..idx.value.1),
                    )
                };

                match name {
                    header::CONTENT_LENGTH => {
                        if let Ok(s) = value.to_str() {
                            if let Ok(len) = s.parse::<u64>() {
                                if len != 0 {
                                    content_length = Some(len);
                                }
                            } else {
                                debug!("illegal Content-Length: {:?}", s);
                                return Err(ParseError::Header);
                            }
                        } else {
                            debug!("illegal Content-Length: {:?}", value);
                            return Err(ParseError::Header);
                        }
                    }
                    // transfer-encoding
                    header::TRANSFER_ENCODING => {
                        if let Ok(s) = value.to_str().map(str::trim) {
                            chunked = s.eq_ignore_ascii_case("chunked");
                        } else {
                            return Err(ParseError::Header);
                        }
                    }
                    // connection keep-alive state
                    header::CONNECTION => {
                        ka = if let Ok(conn) = value.to_str().map(str::trim) {
                            if conn.eq_ignore_ascii_case("keep-alive") {
                                Some(ConnectionType::KeepAlive)
                            } else if conn.eq_ignore_ascii_case("close") {
                                Some(ConnectionType::Close)
                            } else if conn.eq_ignore_ascii_case("upgrade") {
                                Some(ConnectionType::Upgrade)
                            } else {
                                None
                            }
                        } else {
                            None
                        };
                    }
                    header::UPGRADE => {
                        if let Ok(val) = value.to_str().map(str::trim) {
                            if val.eq_ignore_ascii_case("websocket") {
                                has_upgrade_websocket = true;
                            }
                        }
                    }
                    header::EXPECT => {
                        let bytes = value.as_bytes();
                        if bytes.len() >= 4 && &bytes[0..4] == b"100-" {
                            expect = true;
                        }
                    }
                    _ => {}
                }

                headers.append(name, value);
            }
        }
        self.set_connection_type(ka);
        if expect {
            self.set_expect()
        }

        // https://tools.ietf.org/html/rfc7230#section-3.3.3
        if chunked {
            // Chunked encoding
            Ok(PayloadLength::Payload(PayloadType::Payload(
                PayloadDecoder::chunked(),
            )))
        } else if has_upgrade_websocket {
            Ok(PayloadLength::UpgradeWebSocket)
        } else if let Some(len) = content_length {
            // Content-Length
            Ok(PayloadLength::Payload(PayloadType::Payload(
                PayloadDecoder::length(len),
            )))
        } else {
            Ok(PayloadLength::None)
        }
    }
