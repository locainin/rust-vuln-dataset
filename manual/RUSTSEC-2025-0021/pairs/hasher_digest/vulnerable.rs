        pub fn digest(self) -> Digest {
            self.0.digest().bytes()
        }
