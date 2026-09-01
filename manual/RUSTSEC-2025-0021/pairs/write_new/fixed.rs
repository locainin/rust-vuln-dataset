        pub fn new(inner: T, object_hash: crate::Kind) -> Self {
            match object_hash {
                crate::Kind::Sha1 => Write {
                    inner,
                    hash: crate::hasher(object_hash),
                },
            }
        }
