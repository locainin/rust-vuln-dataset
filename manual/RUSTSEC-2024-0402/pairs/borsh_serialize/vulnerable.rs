    fn serialize<W: Write>(&self, writer: &mut W) -> Result<()> {
        // assuming hash may have some seed,
        // as borsh is supposed by default to be deterministic, need to write it down
        // if allocator is compile time, than one can just impl wrapper with zero bytes serde of it
        self.hash_builder.serialize(writer)?;
        // considering A stateless
        self.len().serialize(writer)?;
        for kv in self.iter() {
            kv.serialize(writer)?;
        }
        Ok(())
    }
