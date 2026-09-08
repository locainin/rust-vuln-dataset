    pub async fn read_bytes(mut self) -> crate::Result<Vec<u8>> {
        let mut vec = if let Some(len) = self.content_length {
            if len > self.max_len {
                return Err(crate::Error::ReceivedBodyTooLong(self.max_len));
            }

            let len = usize::try_from(len)
                .map_err(|_| crate::Error::ReceivedBodyTooLong(self.max_len))?;

            Vec::with_capacity(len.min(self.max_preallocate))
        } else {
            Vec::with_capacity(self.initial_len)
        };

        self.read_to_end(&mut vec).await?;
        Ok(vec)
    }
