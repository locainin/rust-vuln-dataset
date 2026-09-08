    fn read_repeated_packed_into<T: ProtobufTypeTrait>(
        &mut self,
        target: &mut Vec<T::ProtobufValue>,
    ) -> crate::Result<()> {
        let len_bytes = self.read_raw_varint64()?;

        // value is at least 1 bytes, so this is lower bound of element count
        let reserve = if len_bytes <= READ_RAW_BYTES_MAX_ALLOC as u64 {
            len_bytes as usize
        } else {
            // prevent OOM on malformed input
            READ_RAW_BYTES_MAX_ALLOC
        };

        target.reserve(reserve);

        let old_limit = self.push_limit(len_bytes)?;
        while !self.eof()? {
            target.push(T::read(self)?);
        }
        self.pop_limit(old_limit);
        Ok(())
    }
