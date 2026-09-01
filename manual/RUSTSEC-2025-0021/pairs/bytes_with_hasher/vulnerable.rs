pub fn bytes_with_hasher(
    read: &mut dyn std::io::Read,
    num_bytes_from_start: u64,
    mut hasher: Hasher,
    progress: &mut dyn crate::progress::Progress,
    should_interrupt: &std::sync::atomic::AtomicBool,
) -> std::io::Result<gix_hash::ObjectId> {
    let start = std::time::Instant::now();
    // init progress before the possibility for failure, as convenience in case people want to recover
    progress.init(
        Some(num_bytes_from_start as prodash::progress::Step),
        crate::progress::bytes(),
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
            return Err(std::io::Error::new(std::io::ErrorKind::Other, "Interrupted"));
        }
    }

    let id = gix_hash::ObjectId::from(hasher.digest());
    progress.show_throughput(start);
    Ok(id)
}
