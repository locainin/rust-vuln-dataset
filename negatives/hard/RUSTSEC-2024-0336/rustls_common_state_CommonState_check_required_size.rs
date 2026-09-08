    fn check_required_size<'a>(
        &self,
        outgoing_tls: &mut [u8],
        opt_msg: Option<&[u8]>,
        fragments: impl Iterator<Item = OutboundPlainMessage<'a>>,
    ) -> Result<(), EncryptError> {
        let mut required_size = 0;
        if let Some(message) = opt_msg {
            required_size += message.len();
        }

        for m in fragments {
            required_size += m.encoded_len(&self.record_layer);
        }

        if required_size > outgoing_tls.len() {
            return Err(EncryptError::InsufficientSize(InsufficientSizeError {
                required_size,
            }));
        }

        Ok(())
    }
