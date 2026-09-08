    fn consume(&mut self, amount: usize) -> &[u8] {
        // println!("Generic.consume({}) \
        //           (cursor: {}, buffer: {:?})",
        //          amount, self.cursor,
        //          if let Some(ref buffer) = self.buffer { Some(buffer.len()) }
        //          else { None });

        // The caller can't consume more than is buffered!
        if let Some(ref buffer) = self.buffer {
            assert!(self.cursor <= buffer.len());
            assert!(amount <= buffer.len() - self.cursor,
                    "buffer contains just {} bytes, but you are trying to \
                    consume {} bytes.  Did you forget to call data()?",
                    buffer.len() - self.cursor, amount);

            self.cursor += amount;
            return &self.buffer.as_ref().unwrap()[self.cursor - amount..];
        } else {
            assert_eq!(amount, 0);
            &b""[..]
        }
    }
