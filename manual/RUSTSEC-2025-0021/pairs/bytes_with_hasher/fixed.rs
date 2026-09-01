    pub fn bytes_with_hasher(
        read: &mut dyn std::io::Read,
        num_bytes_from_start: u64,
        mut hasher: Hasher,
        progress: &mut dyn gix_features::progress::Progress,
        should_interrupt: &std::sync::atomic::AtomicBool,
    ) -> Result<crate::ObjectId, Error> {
        let start = std::time::Instant::now();
        // init progress before the possibility for failure, as convenience in case people want to recover
        progress.init(
            Some(num_bytes_from_start as gix_features::progress::prodash::progress::Step),
            gix_features::progress::bytes(),
        );

        const BUF_SIZE: usize = u16::MAX as usize;
        let mut buf = [0u8; BUF_SIZE];
        let mut bytes_left = num_bytes_from_start;

        while bytes_left > 0 {
            let out = &mut buf[..BUF_SIZE.min(bytes_left as usize)];
            read.read_exact(out)?;
            bytes_left -= out.len() as u64;
            progress.inc_by(out.len());
            hasher.update(out);
            if should_interrupt.load(std::sync::atomic::Ordering::SeqCst) {
                return Err(std::io::Error::new(std::io::ErrorKind::Other, "Interrupted").into());
            }
        }

        let id = hasher.try_finalize()?;
        progress.show_throughput(start);
        Ok(id)
    }
