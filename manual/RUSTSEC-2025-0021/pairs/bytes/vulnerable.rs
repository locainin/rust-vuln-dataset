pub fn bytes(
    read: &mut dyn std::io::Read,
    num_bytes_from_start: u64,
    kind: gix_hash::Kind,
    progress: &mut dyn crate::progress::Progress,
    should_interrupt: &std::sync::atomic::AtomicBool,
) -> std::io::Result<gix_hash::ObjectId> {
    bytes_with_hasher(read, num_bytes_from_start, hasher(kind), progress, should_interrupt)
}
