    pub fn abort(&self) {
        if let Some(raw) = self.raw {
            raw.remote_abort();
        }
    }
