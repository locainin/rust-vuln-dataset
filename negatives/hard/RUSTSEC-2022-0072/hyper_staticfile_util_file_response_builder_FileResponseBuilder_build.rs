    pub fn build<F: IntoFileAccess>(
        &self,
        file: ResolvedFile<F>,
    ) -> Result<Response<Body<F::Output>>> {
        let mut res = ResponseBuilder::new();

        // Set `Last-Modified` and check `If-Modified-Since`.
        let modified = file.modified.filter(|v| {
            v.duration_since(UNIX_EPOCH)
                .ok()
                .filter(|v| v >= &MIN_VALID_MTIME)
                .is_some()
        });

        // default to false when specified, either the etag or last_modified will set
        // it to true later.
        let mut range_cond_ok = self.if_range.is_none();
        if let Some(modified) = modified {
            if let Ok(modified_unix) = modified.duration_since(UNIX_EPOCH) {
                // Compare whole seconds only, because the HTTP date-time
                // format also does not contain a fractional part.
                if let Some(Ok(ims_unix)) =
                    self.if_modified_since.map(|v| v.duration_since(UNIX_EPOCH))
                {
                    if modified_unix.as_secs() <= ims_unix.as_secs() {
                        return ResponseBuilder::new()
                            .status(StatusCode::NOT_MODIFIED)
                            .body(Body::Empty);
                    }
                }

                let etag = format!(
                    "W/\"{0:x}-{1:x}.{2:x}\"",
                    file.size,
                    modified_unix.as_secs(),
                    modified_unix.subsec_nanos()
                );
                if let Some(ref v) = self.if_range {
                    if *v == etag {
                        range_cond_ok = true;
                    }
                }

                res = res.header(header::ETAG, etag);
            }

            let last_modified_formatted = httpdate::fmt_http_date(modified);
            if let Some(ref v) = self.if_range {
                if *v == last_modified_formatted {
                    range_cond_ok = true;
                }
            }

            res = res
                .header(header::LAST_MODIFIED, last_modified_formatted)
                .header(header::ACCEPT_RANGES, "bytes");
        }

        // Build remaining headers.
        if let Some(seconds) = self.cache_headers {
            res = res.header(
                header::CACHE_CONTROL,
                format!("public, max-age={}", seconds),
            );
        }

        if self.is_head {
            res = res.header(header::CONTENT_LENGTH, format!("{}", file.size));
            return res.status(StatusCode::OK).body(Body::Empty);
        }

        let ranges = self.range.as_ref().filter(|_| range_cond_ok).and_then(|r| {
            match HttpRange::parse(r, file.size) {
                Ok(r) => Some(Ok(r)),
                Err(HttpRangeParseError::NoOverlap) => Some(Err(())),
                Err(HttpRangeParseError::InvalidRange) => None,
            }
        });

        if let Some(ranges) = ranges {
            let ranges = match ranges {
                Ok(r) => r,
                Err(()) => {
                    return res
                        .status(StatusCode::RANGE_NOT_SATISFIABLE)
                        .body(Body::Empty);
                }
            };

            if ranges.len() == 1 {
                let single_span = ranges[0];
                res = res
                    .header(
                        header::CONTENT_RANGE,
                        content_range_header(&single_span, file.size),
                    )
                    .header(header::CONTENT_LENGTH, format!("{}", single_span.length));

                let body_stream =
                    FileBytesStreamRange::new(file.handle.into_file_access(), single_span);
                return res
                    .status(StatusCode::PARTIAL_CONTENT)
                    .body(Body::Range(body_stream));
            } else if ranges.len() > 1 {
                let mut boundary_tmp = [0u8; BOUNDARY_LENGTH];

                let mut rng = thread_rng();
                for v in boundary_tmp.iter_mut() {
                    // won't panic since BOUNDARY_CHARS is non-empty
                    *v = *BOUNDARY_CHARS.choose(&mut rng).unwrap();
                }

                // won't panic because boundary_tmp is guaranteed to be all ASCII
                let boundary = std::str::from_utf8(&boundary_tmp[..]).unwrap().to_string();

                res = res.header(
                    hyper::header::CONTENT_TYPE,
                    format!("multipart/byteranges; boundary={}", boundary),
                );

                let mut body_stream = FileBytesStreamMultiRange::new(
                    file.handle.into_file_access(),
                    ranges,
                    boundary,
                    file.size,
                );
                if let Some(content_type) = file.content_type.as_ref() {
                    body_stream.set_content_type(content_type);
                }

                res = res.header(
                    hyper::header::CONTENT_LENGTH,
                    format!("{}", body_stream.compute_length()),
                );

                return res
                    .status(StatusCode::PARTIAL_CONTENT)
                    .body(Body::MultiRange(body_stream));
            }
        }

        res = res.header(header::CONTENT_LENGTH, format!("{}", file.size));
        if let Some(content_type) = file.content_type {
            res = res.header(header::CONTENT_TYPE, content_type);
        }
        if let Some(encoding) = file.encoding {
            res = res.header(header::CONTENT_ENCODING, encoding.to_header_value());
        }

        // Stream the body.
        res.status(StatusCode::OK)
            .body(Body::Full(FileBytesStream::new_with_limit(
                file.handle.into_file_access(),
                file.size,
            )))
    }
