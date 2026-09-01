        pub fn digest(self) -> super::Digest {
            self.0.finalize().into()
        }
