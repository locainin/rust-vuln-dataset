    #[inline]
    pub fn split_off(&mut self, k: usize) -> Option<Vec<T, A>> {
        assert!(k <= self.len, "out of bounds");
        let mut xs = Vec::with_capacity_in(self.raw.alloc.try_clone().ok()?, self.len - k)?;
        unsafe {
            xs.len = self.len - k;
            self.len = k;
            ptr::copy_nonoverlapping(self.ptr().add(k), xs.ptr(), xs.len);
        }
        Some(xs)
    }
