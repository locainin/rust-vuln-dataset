    #[corresponds(X509_VERIFY_PARAM_set1_host)]
    pub fn set_host(&mut self, host: &str) -> Result<(), ErrorStack> {
        unsafe {
            // len == 0 means "run strlen" :(
            let raw_host = if host.is_empty() { "\0" } else { host };
            cvt(ffi::X509_VERIFY_PARAM_set1_host(
                self.as_ptr(),
                raw_host.as_ptr() as *const _,
                host.len(),
            ))
            .map(|_| ())
        }
    }
