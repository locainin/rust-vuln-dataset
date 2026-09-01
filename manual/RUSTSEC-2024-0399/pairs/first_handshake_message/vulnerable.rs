    pub(crate) fn first_handshake_message(&mut self) -> Result<Option<Message<'static>>, Error> {
        let mut buffer_progress = BufferProgress::default();

        let res = self
            .core
            .deframe(
                None,
                self.deframer_buffer.filled_mut(),
                &mut buffer_progress,
            )
            .map(|opt| opt.map(|pm| Message::try_from(pm).map(|m| m.into_owned())));

        match res? {
            Some(Ok(msg)) => {
                self.deframer_buffer
                    .discard(buffer_progress.take_discard());
                Ok(Some(msg))
            }
            Some(Err(err)) => Err(self.send_fatal_alert(AlertDescription::DecodeError, err)),
            None => Ok(None),
        }
    }
