    fn for_each<F>(&self, mut f: F)
    where
        F: for<'a> FnMut(&'a SliceSource<T>),
    {
        for source in self.as_slice() {
            f(source);
        }
    }
