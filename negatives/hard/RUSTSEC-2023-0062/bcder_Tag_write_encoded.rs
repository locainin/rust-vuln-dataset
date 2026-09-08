    #[allow(clippy::trivially_copy_pass_by_ref)] // for possible multi-byte tags
    pub fn write_encoded<W: io::Write>(
        &self,
        constructed: bool,
        target: &mut W
    ) -> Result<(), io::Error> {
        let mut buf = self.0;
        if constructed {
            buf[0] |= Tag::CONSTRUCTED_MASK
        }
        target.write_all(&buf[..self.encoded_len()])
    }
