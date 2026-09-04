    fn read_size(
        rdr: &mut BytesMut,
        size: &mut u64,
    ) -> Poll<Result<ChunkedState, io::Error>> {
        let radix = 16;
        match byte!(rdr) {
            b @ b'0'..=b'9' => {
                *size *= radix;
                *size += u64::from(b - b'0');
            }
            b @ b'a'..=b'f' => {
                *size *= radix;
                *size += u64::from(b + 10 - b'a');
            }
            b @ b'A'..=b'F' => {
                *size *= radix;
                *size += u64::from(b + 10 - b'A');
            }
            b'\t' | b' ' => return Poll::Ready(Ok(ChunkedState::SizeLws)),
            b';' => return Poll::Ready(Ok(ChunkedState::Extension)),
            b'\r' => return Poll::Ready(Ok(ChunkedState::SizeLf)),
            _ => {
                return Poll::Ready(Err(io::Error::new(
                    io::ErrorKind::InvalidInput,
                    "Invalid chunk size line: Invalid Size",
                )));
            }
        }
        Poll::Ready(Ok(ChunkedState::Size))
    }
