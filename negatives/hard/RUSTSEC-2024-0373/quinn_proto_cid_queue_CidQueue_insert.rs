    pub(crate) fn insert(
        &mut self,
        cid: NewConnectionId,
    ) -> Result<Option<(Range<u64>, ResetToken)>, InsertError> {
        // Position of new CID wrt. the current active CID
        let index = match cid.sequence.checked_sub(self.offset) {
            None => return Err(InsertError::Retired),
            Some(x) => x,
        };

        let retired_count = cid.retire_prior_to.saturating_sub(self.offset);
        if index >= Self::LEN as u64 + retired_count {
            return Err(InsertError::ExceedsLimit);
        }

        // Discard retired CIDs, if any
        for i in 0..(retired_count.min(Self::LEN as u64) as usize) {
            self.buffer[(self.cursor + i) % Self::LEN] = None;
        }

        // Record the new CID
        let index = ((self.cursor as u64 + index) % Self::LEN as u64) as usize;
        self.buffer[index] = Some((cid.id, Some(cid.reset_token)));

        if retired_count == 0 {
            return Ok(None);
        }

        // The active CID was retired. Find the first known CID with sequence number of at least
        // retire_prior_to, and inform the caller that all prior CIDs have been retired, and of
        // the new CID's reset token.
        self.cursor = ((self.cursor as u64 + retired_count) % Self::LEN as u64) as usize;
        let (i, (_, token)) = self
            .iter()
            .next()
            .expect("it is impossible to retire a CID without supplying a new one");
        self.cursor = (self.cursor + i) % Self::LEN;
        let orig_offset = self.offset;
        self.offset = cid.retire_prior_to + i as u64;
        // We don't immediately retire CIDs in the range (orig_offset +
        // Self::LEN)..self.offset. These are CIDs that we haven't yet received from a
        // NEW_CONNECTION_ID frame, since having previously received them would violate the
        // connection ID limit we specified based on Self::LEN. If we do receive a such a frame
        // in the future, e.g. due to reordering, we'll retire it then. This ensures we can't be
        // made to buffer an arbitrarily large number of RETIRE_CONNECTION_ID frames.
        Ok(Some((
            orig_offset..self.offset.min(orig_offset + Self::LEN as u64),
            token.expect("non-initial CID missing reset token"),
        )))
    }
