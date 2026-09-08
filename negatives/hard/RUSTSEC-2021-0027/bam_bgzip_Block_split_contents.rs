    pub fn split_contents(&mut self, first_size: usize, second_part: &mut [u8]) -> usize {
        assert!(self.uncompressed.len() >= first_size,
            "Cannot split a block with: size {} < {}", self.uncompressed.len(), first_size);
        assert!(self.compressed.is_empty(), "Cannot split an already compressed block");

        let second_size = self.uncompressed.len() - first_size;
        second_part[..second_size].copy_from_slice(&self.uncompressed[first_size..]);
        self.uncompressed.truncate(first_size);
        second_size
    }
