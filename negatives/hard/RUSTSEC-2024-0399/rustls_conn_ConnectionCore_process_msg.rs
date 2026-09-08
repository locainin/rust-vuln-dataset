    fn process_msg(
        &mut self,
        msg: InboundPlainMessage<'_>,
        state: Box<dyn State<Data>>,
        sendable_plaintext: Option<&mut ChunkVecBuffer>,
    ) -> Result<Box<dyn State<Data>>, Error> {
        // Drop CCS messages during handshake in TLS1.3
        if msg.typ == ContentType::ChangeCipherSpec
            && !self
                .common_state
                .may_receive_application_data
            && self.common_state.is_tls13()
        {
            if !msg.is_valid_ccs() {
                // "An implementation which receives any other change_cipher_spec value or
                //  which receives a protected change_cipher_spec record MUST abort the
                //  handshake with an "unexpected_message" alert."
                return Err(self.common_state.send_fatal_alert(
                    AlertDescription::UnexpectedMessage,
                    PeerMisbehaved::IllegalMiddleboxChangeCipherSpec,
                ));
            }

            self.common_state
                .received_tls13_change_cipher_spec()?;
            trace!("Dropping CCS");
            return Ok(state);
        }

        // Now we can fully parse the message payload.
        let msg = match Message::try_from(msg) {
            Ok(msg) => msg,
            Err(err) => {
                return Err(self
                    .common_state
                    .send_fatal_alert(AlertDescription::DecodeError, err));
            }
        };

        // For alerts, we have separate logic.
        if let MessagePayload::Alert(alert) = &msg.payload {
            self.common_state.process_alert(alert)?;
            return Ok(state);
        }

        self.common_state
            .process_main_protocol(msg, state, &mut self.data, sendable_plaintext)
    }
