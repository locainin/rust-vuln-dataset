    pub fn skip_if<S: Source>(
        &self, constructed: &mut Constructed<S>,
    ) -> Result<(), DecodeError<S::Error>> {
        constructed.take_primitive_if(Tag::OID, |content| {
            let len = content.remaining();
            content.request(len)?;
            if &content.slice()[..len] == self.0.as_ref() {
                content.skip_all()?;
                Ok(())
            }
            else {
                Err(content.content_err("object identifier mismatch"))
            }
        })
    }
