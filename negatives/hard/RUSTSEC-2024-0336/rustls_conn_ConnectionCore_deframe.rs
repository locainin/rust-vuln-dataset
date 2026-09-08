    fn deframe<'b>(
        &mut self,
        state: Option<&dyn State<Data>>,
        deframer_buffer: &mut DeframerSliceBuffer<'b>,
    ) -> Result<Option<InboundPlainMessage<'b>>, Error> {
        match self.message_deframer.pop(
            &mut self.common_state.record_layer,
            self.common_state.negotiated_version,
            deframer_buffer,
        ) {
            Ok(Some(Deframed {
                want_close_before_decrypt,
                aligned,
                trial_decryption_finished,
                message,
            })) => {
                if want_close_before_decrypt {
                    self.common_state.send_close_notify();
                }

                if trial_decryption_finished {
                    self.common_state
                        .record_layer
                        .finish_trial_decryption();
                }

                self.common_state.aligned_handshake = aligned;
                Ok(Some(message))
            }
            Ok(None) => Ok(None),
            Err(err @ Error::InvalidMessage(_)) => {
                if self.common_state.is_quic() {
                    self.common_state.quic.alert = Some(AlertDescription::DecodeError);
                }

                Err(if !self.common_state.is_quic() {
                    self.common_state
                        .send_fatal_alert(AlertDescription::DecodeError, err)
                } else {
                    err
                })
            }
            Err(err @ Error::PeerSentOversizedRecord) => Err(self
                .common_state
                .send_fatal_alert(AlertDescription::RecordOverflow, err)),
            Err(err @ Error::DecryptError) => {
                if let Some(state) = state {
                    state.handle_decrypt_error();
                }
                Err(self
                    .common_state
                    .send_fatal_alert(AlertDescription::BadRecordMac, err))
            }
            Err(e) => Err(e),
        }
    }
