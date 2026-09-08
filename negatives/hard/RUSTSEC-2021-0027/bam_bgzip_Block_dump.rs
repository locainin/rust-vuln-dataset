    pub fn dump<W: Write>(&self, stream: &mut W) -> io::Result<()> {
        assert!(!self.compressed.is_empty(), "Cannot write an uncompressed block");
        let block_size = self.block_size().expect("Block size should be defined already") - 1;
        let block_header: &[u8; 18] = &[
            31, 139,   8,   4,  // ID1, ID2, Compression method, Flags
             0,   0,   0,   0,  // Modification time
             0, 255,   6,   0,  // Extra flags, OS (255 = unknown), extra length (2 bytes)
            66,  67,   2,   0, // SI1, SI2, subfield len (2 bytes)
            block_size as u8, (block_size >> 8) as u8];
        stream.write_all(block_header)?;
        stream.write_all(&self.compressed)
    }
