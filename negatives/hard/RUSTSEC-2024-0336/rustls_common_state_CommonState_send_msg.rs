    pub(crate) fn send_msg(&mut self, m: Message, must_encrypt: bool) {
        {
            if let Protocol::Quic = self.protocol {
                if let MessagePayload::Alert(alert) = m.payload {
                    self.quic.alert = Some(alert.description);
                } else {
                    debug_assert!(
                        matches!(m.payload, MessagePayload::Handshake { .. }),
                        "QUIC uses TLS for the cryptographic handshake only"
                    );
                    let mut bytes = Vec::new();
                    m.payload.encode(&mut bytes);
                    self.quic
                        .hs_queue
                        .push_back((must_encrypt, bytes));
                }
                return;
            }
        }
        if !must_encrypt {
            let msg = &m.into();
            let iter = self
                .message_fragmenter
                .fragment_message(msg);
            for m in iter {
                self.queue_tls_message(m.to_unencrypted_opaque());
            }
        } else {
            self.send_msg_encrypt(m.into());
        }
    }
