    pub fn get_bucket(&self, index: u32) -> u32 {
        assert!(index < self.bucket_count);
        unsafe {
            let ptr = (&self.first_bucket as *const u32).offset(index as isize);
            *ptr
        }
    }
