    fn read_extension(rdr: &mut BytesMut) -> Poll<Result<ChunkedState, io::Error>> {
        match byte!(rdr) {
            b'\r' => Poll::Ready(Ok(ChunkedState::SizeLf)),
            _ => Poll::Ready(Ok(ChunkedState::Extension)), // no supported extensions
        }
    }
