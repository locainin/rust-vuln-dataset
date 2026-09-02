    pub fn skip_if<S: Source>(
        &self, constructed: &mut Constructed<S>,
    ) -> Result<(), DecodeError<S::Error>> {
        constructed.take_primitive_if(Tag::OID, |prim| {
            prim.with_slice_all(|content| {
                // We are assuming that self contains a properly encoded OID,
                // so we don’t really need to check if prim does, too, if we
                // compare for equality.
                if content != self.0.as_ref() {
                    Err("object identifier mismatch")
                }
                else {
                    Ok(())
                }
            })
        })
    }
