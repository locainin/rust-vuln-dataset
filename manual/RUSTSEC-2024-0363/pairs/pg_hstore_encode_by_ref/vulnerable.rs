    fn encode_by_ref(&self, buf: &mut PgArgumentBuffer) -> Result<IsNull, BoxDynError> {
        buf.extend_from_slice(&i32::to_be_bytes(self.0.len() as i32));

        for (key, val) in &self.0 {
            let key_bytes = key.as_bytes();

            buf.extend_from_slice(&i32::to_be_bytes(key_bytes.len() as i32));
            buf.extend_from_slice(key_bytes);

            match val {
                Some(val) => {
                    let val_bytes = val.as_bytes();

                    buf.extend_from_slice(&i32::to_be_bytes(val_bytes.len() as i32));
                    buf.extend_from_slice(val_bytes);
                }
                None => {
                    buf.extend_from_slice(&i32::to_be_bytes(-1));
                }
            }
        }

        Ok(IsNull::No)
    }
