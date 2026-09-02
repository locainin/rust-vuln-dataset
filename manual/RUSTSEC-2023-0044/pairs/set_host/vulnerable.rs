    #[corresponds(X509_VERIFY_PARAM_set1_host)]
    pub fn set_host(&mut self, host: &str) -> Result<(), ErrorStack> {
        unsafe {
            cvt(ffi::X509_VERIFY_PARAM_set1_host(
                self.as_ptr(),
                host.as_ptr() as *const _,
                host.len(),
            ))
            .map(|_| ())
        }
    }
