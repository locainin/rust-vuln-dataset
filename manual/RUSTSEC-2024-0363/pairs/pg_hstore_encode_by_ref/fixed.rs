    fn encode_by_ref(&self, buf: &mut PgArgumentBuffer) -> Result<IsNull, BoxDynError> {
        buf.extend_from_slice(&i32::to_be_bytes(
            self.0
                .len()
                .try_into()
                .map_err(|_| format!("PgHstore length out of range: {}", self.0.len()))?,
        ));

        for (i, (key, val)) in self.0.iter().enumerate() {
            let key_bytes = key.as_bytes();

            let key_len = i32::try_from(key_bytes.len()).map_err(|_| {
                // Doesn't make sense to print the key itself: it's more than 2 GiB long!
                format!(
                    "PgHstore: length of {i}th key out of range: {} bytes",
                    key_bytes.len()
                )
            })?;

            buf.extend_from_slice(&i32::to_be_bytes(key_len));
            buf.extend_from_slice(key_bytes);

            match val {
                Some(val) => {
                    let val_bytes = val.as_bytes();

                    let val_len = i32::try_from(val_bytes.len()).map_err(|_| {
                        format!(
                            "PgHstore: value length for key {key:?} out of range: {} bytes",
                            val_bytes.len()
                        )
                    })?;
                    buf.extend_from_slice(&i32::to_be_bytes(val_len));
                    buf.extend_from_slice(val_bytes);
                }
                None => {
                    buf.extend_from_slice(&i32::to_be_bytes(-1));
                }
            }
        }

        Ok(IsNull::No)
    }
