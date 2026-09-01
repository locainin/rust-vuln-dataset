    fn skip_group(&mut self) -> crate::Result<()> {
        while !self.eof()? {
            let wire_type = self.read_tag_unpack()?.1;
            if wire_type == WireType::EndGroup {
                break;
            }
            self.skip_field(wire_type)?;
        }
        Ok(())
    }
