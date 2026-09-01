    pub fn get_bucket(&self, index: u32) -> u32 {
        assert!(index < self.inner.bucket_count);
        assert!((index as usize) < self.bounds);
        unsafe {
            let ptr = (&self.inner.first_bucket as *const u32).offset(index as isize);
            *ptr
        }
    }
