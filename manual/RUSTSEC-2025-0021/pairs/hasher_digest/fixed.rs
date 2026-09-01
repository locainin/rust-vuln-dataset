        pub fn try_finalize(self) -> Result<crate::ObjectId, Error> {
            match self.0.try_finalize() {
                CollisionResult::Ok(digest) => Ok(crate::ObjectId::Sha1(digest.into())),
                CollisionResult::Mitigated(_) => {
                    // SAFETY: `CollisionResult::Mitigated` is only
                    // returned when `safe_hash()` is on. `Hasher`’s field
                    // is private, and we only construct it in the
                    // `Default` instance, which turns `safe_hash()` off.
                    //
                    // As of Rust 1.84.1, the compiler can’t figure out
                    // this function cannot panic without this.
                    #[allow(unsafe_code)]
                    unsafe {
                        std::hint::unreachable_unchecked()
                    }
                }
                CollisionResult::Collision(digest) => Err(Error::CollisionAttack {
                    digest: crate::ObjectId::Sha1(digest.into()),
                }),
            }
        }
