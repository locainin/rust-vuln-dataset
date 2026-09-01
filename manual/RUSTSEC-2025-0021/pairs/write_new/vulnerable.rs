        pub fn new(inner: T, object_hash: gix_hash::Kind) -> Self {
            match object_hash {
                gix_hash::Kind::Sha1 => Write {
                    inner,
                    hash: Hasher::default(),
                },
            }
        }
