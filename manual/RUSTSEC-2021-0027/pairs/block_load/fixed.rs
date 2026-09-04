    pub fn load<R: Read>(&mut self, offset: Option<u64>, stream: &mut R) -> Result<(), BlockError> {
        assert!(self.compressed.is_empty() && self.uncompressed.is_empty(),
            "Cannot load into a non-empty block");
        self.offset = offset;

        let extra_len = {
            self.buffer.resize(HEADER_SIZE + MIN_EXTRA_SIZE, 0);
            match stream.read_exact(&mut self.buffer) {
                Ok(()) => {},
                Err(e) => {
                    if e.kind() == ErrorKind::UnexpectedEof {
                        return Err(BlockError::EndOfStream);
                    } else {
                        return Err(BlockError::from(e));
                    }
                }
            }
            analyze_header(&self.buffer)? as usize
        };

        if extra_len > MIN_EXTRA_SIZE {
            self.buffer.resize(HEADER_SIZE + extra_len, 0);
            stream.read_exact(&mut self.buffer[HEADER_SIZE..])?;
        }
        let block_size = analyze_extra_fields(&self.buffer[HEADER_SIZE..])? as usize + 1;
        if block_size > MAX_BLOCK_SIZE || block_size < HEADER_SIZE + MIN_EXTRA_SIZE {
            return Err(BlockError::Corrupted(
                format!("Block size {} > {} or < {}", block_size, MAX_BLOCK_SIZE, HEADER_SIZE + MIN_EXTRA_SIZE)));
        }

        unsafe {
            // Include footer in self.compressed to read footer in one go.
            self.compressed.set_len(block_size - HEADER_SIZE - MIN_EXTRA_SIZE);
        }
        stream.read_exact(&mut self.compressed)?;
        Ok(())
    }
