    fn read_size(
        rdr: &mut BytesMut,
        size: &mut u64,
    ) -> Poll<Result<ChunkedState, io::Error>> {
        let radix = 16;

        let rem = match byte!(rdr) {
            b @ b'0'..=b'9' => b - b'0',
            b @ b'a'..=b'f' => b + 10 - b'a',
            b @ b'A'..=b'F' => b + 10 - b'A',
            b'\t' | b' ' => return Poll::Ready(Ok(ChunkedState::SizeLws)),
            b';' => return Poll::Ready(Ok(ChunkedState::Extension)),
            b'\r' => return Poll::Ready(Ok(ChunkedState::SizeLf)),
            _ => {
                return Poll::Ready(Err(io::Error::new(
                    io::ErrorKind::InvalidInput,
                    "Invalid chunk size line: Invalid Size",
                )));
            }
        };

        match size.checked_mul(radix) {
            Some(n) => {
                *size = n as u64;
                *size += rem as u64;

                Poll::Ready(Ok(ChunkedState::Size))
            }
            None => {
                log::debug!("chunk size would overflow u64");
                Poll::Ready(Err(io::Error::new(
                    io::ErrorKind::InvalidInput,
                    "Invalid chunk size line: Size is too big",
                )))
            }
        }
    }
