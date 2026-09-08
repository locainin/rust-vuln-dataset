    fn flush_plaintext(&mut self, sendable_plaintext: &mut ChunkVecBuffer) {
        if !self.may_send_application_data {
            return;
        }

        while let Some(buf) = sendable_plaintext.pop() {
            self.send_plain_non_buffering(buf.as_slice().into(), Limit::No);
        }
    }
