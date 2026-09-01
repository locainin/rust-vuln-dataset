    pub fn bytes_of_file(
        path: &std::path::Path,
        num_bytes_from_start: u64,
        kind: crate::Kind,
        progress: &mut dyn gix_features::progress::Progress,
        should_interrupt: &std::sync::atomic::AtomicBool,
    ) -> Result<crate::ObjectId, Error> {
        bytes(
            &mut std::fs::File::open(path)?,
            num_bytes_from_start,
            kind,
            progress,
            should_interrupt,
        )
    }
