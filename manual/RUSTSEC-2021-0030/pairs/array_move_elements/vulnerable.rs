    fn move_elements<F>(self, mut f: F)
    where
        F: FnMut(<T as Array>::Item),
    {
        unsafe {
            for item in self.as_slice() {
                f(ptr::read(item))
            }

            forget(self);
        }
    }
