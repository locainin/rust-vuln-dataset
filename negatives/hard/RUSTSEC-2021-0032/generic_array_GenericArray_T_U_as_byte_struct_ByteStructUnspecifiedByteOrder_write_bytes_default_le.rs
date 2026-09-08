    fn write_bytes_default_le(&self, bytes: &mut [u8]) {
        let mut pos = 0;
        let len = T::BYTE_LEN;
        for i in 0 .. U::USIZE {
            self[i].write_bytes_default_le(&mut bytes[pos .. pos + len]);
            pos += len;
        }
    }
