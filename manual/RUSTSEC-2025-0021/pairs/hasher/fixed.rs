    pub fn hasher(kind: crate::Kind) -> Hasher {
        match kind {
            crate::Kind::Sha1 => Hasher::default(),
        }
    }
