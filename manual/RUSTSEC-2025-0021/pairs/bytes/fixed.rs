    pub fn bytes(
        read: &mut dyn std::io::Read,
        num_bytes_from_start: u64,
        kind: crate::Kind,
        progress: &mut dyn gix_features::progress::Progress,
        should_interrupt: &std::sync::atomic::AtomicBool,
    ) -> Result<crate::ObjectId, Error> {
        bytes_with_hasher(read, num_bytes_from_start, hasher(kind), progress, should_interrupt)
    }
