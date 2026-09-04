    fn extend<I: iter::IntoIterator<Item=A::Item>>(&mut self, iterable: I) {
        // size_hint() has no safety guarantees, and TrustedLen
        // is nightly only, so we can't do any optimizations with
        // size_hint.
        for elem in iterable.into_iter() {
            self.push(elem);
        }
    }
