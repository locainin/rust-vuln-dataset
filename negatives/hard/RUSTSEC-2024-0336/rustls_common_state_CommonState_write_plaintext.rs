    pub(crate) fn write_plaintext(
        &mut self,
        payload: OutboundChunks<'_>,
        outgoing_tls: &mut [u8],
    ) -> Result<usize, EncryptError> {
        if payload.is_empty() {
            return Ok(0);
        }

        let fragments = self
            .message_fragmenter
            .fragment_payload(
                ContentType::ApplicationData,
                ProtocolVersion::TLSv1_2,
                payload.clone(),
            );

        let remaining_encryptions = self
            .record_layer
            .remaining_write_seq()
            .ok_or(EncryptError::EncryptExhausted)?;

        if fragments.len() as u64 > remaining_encryptions.get() {
            return Err(EncryptError::EncryptExhausted);
        }

        self.check_required_size(
            outgoing_tls,
            self.queued_key_update_message
                .as_deref(),
            fragments,
        )?;

        let fragments = self
            .message_fragmenter
            .fragment_payload(
                ContentType::ApplicationData,
                ProtocolVersion::TLSv1_2,
                payload,
            );

        let opt_msg = self.queued_key_update_message.take();
        let written = self.write_fragments(outgoing_tls, opt_msg, fragments);

        Ok(written)
    }
