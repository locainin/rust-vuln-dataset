    pub fn get_buf(&self) -> &[u8] {
        unsafe {
            let mut ptr = ptr::null_mut();
            let len = ffi::BIO_get_mem_data(self.0, &mut ptr);
            if len == 0 {
                &[]
            } else {
                slice::from_raw_parts(ptr as *const _ as *const _, len as usize)
            }
        }
    }
