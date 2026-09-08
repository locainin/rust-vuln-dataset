    pub(crate) fn process_new_packets(
        &mut self,
        deframer_buffer: &mut DeframerVecBuffer,
        sendable_plaintext: &mut ChunkVecBuffer,
    ) -> Result<IoState, Error> {
        let mut state = match mem::replace(&mut self.state, Err(Error::HandshakeNotComplete)) {
            Ok(state) => state,
            Err(e) => {
                self.state = Err(e.clone());
                return Err(e);
            }
        };

        let mut buffer_progress = BufferProgress::default();
        buffer_progress.add_processed(deframer_buffer.processed);

        loop {
            let res = self.deframe(
                Some(&*state),
                deframer_buffer.filled_mut(),
                &mut buffer_progress,
            );

            let opt_msg = match res {
                Ok(opt_msg) => opt_msg,
                Err(e) => {
                    self.state = Err(e.clone());
                    deframer_buffer.discard(buffer_progress.take_discard());
                    return Err(e);
                }
            };

            let Some(msg) = opt_msg else {
                break;
            };

            match self.process_msg(msg, state, Some(sendable_plaintext)) {
                Ok(new) => state = new,
                Err(e) => {
                    self.state = Err(e.clone());
                    deframer_buffer.discard(buffer_progress.take_discard());
                    return Err(e);
                }
            }

            if self
                .common_state
                .has_received_close_notify
            {
                // "Any data received after a closure alert has been received MUST be ignored."
                // -- <https://datatracker.ietf.org/doc/html/rfc8446#section-6.1>
                // This is data that has already been accepted in `read_tls`.
                buffer_progress.add_discard(deframer_buffer.filled().len());
                break;
            }

            deframer_buffer.discard(buffer_progress.take_discard());
        }

        deframer_buffer.processed = buffer_progress.processed();
        deframer_buffer.discard(buffer_progress.take_discard());
        self.state = Ok(state);
        Ok(self.common_state.current_io_state())
    }
