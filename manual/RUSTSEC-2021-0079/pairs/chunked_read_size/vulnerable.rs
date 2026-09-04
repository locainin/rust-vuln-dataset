    fn read_size<R: MemRead>(
        cx: &mut task::Context<'_>,
        rdr: &mut R,
        size: &mut u64,
    ) -> Poll<Result<ChunkedState, io::Error>> {
        trace!("Read chunk hex size");
        let radix = 16;
        match byte!(rdr, cx) {
            b @ b'0'..=b'9' => {
                *size *= radix;
                *size += (b - b'0') as u64;
            }
            b @ b'a'..=b'f' => {
                *size *= radix;
                *size += (b + 10 - b'a') as u64;
            }
            b @ b'A'..=b'F' => {
                *size *= radix;
                *size += (b + 10 - b'A') as u64;
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
