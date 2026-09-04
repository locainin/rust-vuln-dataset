    fn move_elements<F>(self, mut f: F)
    where
        F: FnMut(<T as Array>::Item),
    {
        for item in ArrayIter::new(self) {
            f(item);
        }
    }
