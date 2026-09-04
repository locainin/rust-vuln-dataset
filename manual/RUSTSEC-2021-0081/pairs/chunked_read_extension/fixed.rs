    fn read_extension(rdr: &mut BytesMut) -> Poll<Result<ChunkedState, io::Error>> {
        match byte!(rdr) {
            b'\r' => Poll::Ready(Ok(ChunkedState::SizeLf)),
            // strictly 0x20 (space) should be disallowed but we don't parse quoted strings here
            0x00..=0x08 | 0x0a..=0x1f | 0x7f => Poll::Ready(Err(io::Error::new(
                io::ErrorKind::InvalidInput,
                "Invalid character in chunk extension",
            ))),
            _ => Poll::Ready(Ok(ChunkedState::Extension)), // no supported extensions
        }
    }
