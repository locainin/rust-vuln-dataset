pub fn bytes_of_file(
    path: &std::path::Path,
    num_bytes_from_start: u64,
    kind: gix_hash::Kind,
    progress: &mut dyn crate::progress::Progress,
    should_interrupt: &std::sync::atomic::AtomicBool,
) -> std::io::Result<gix_hash::ObjectId> {
    bytes(
        &mut std::fs::File::open(path)?,
        num_bytes_from_start,
        kind,
        progress,
        should_interrupt,
    )
}
