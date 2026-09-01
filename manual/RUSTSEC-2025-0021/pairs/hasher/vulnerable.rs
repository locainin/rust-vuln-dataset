pub fn hasher(kind: gix_hash::Kind) -> Hasher {
    match kind {
        gix_hash::Kind::Sha1 => Hasher::default(),
    }
}
