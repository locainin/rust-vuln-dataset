    fn discard_exact(&mut self, mut len: usize) -> io::Result<()> {
        while len > 0 {
            let consume_len = match self.fill_buf() {
                Ok(buf) => buf.len().min(len),
                Err(e) if e.kind() == io::ErrorKind::Interrupted => continue,
                Err(e) => return Err(e),
            };
            self.consume(consume_len);
            len -= consume_len;
        }
        Ok(())
    }
