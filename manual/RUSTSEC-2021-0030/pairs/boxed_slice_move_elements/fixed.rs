    fn move_elements<F>(self, mut f: F)
    where
        F: FnMut(<T as SliceLike>::Element),
    {
        for item in vec_from_boxed_slice_like(self) {
            f(item);
        }
    }
