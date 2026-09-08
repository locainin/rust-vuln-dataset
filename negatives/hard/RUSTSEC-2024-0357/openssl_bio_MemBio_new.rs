    pub fn new() -> Result<MemBio, ErrorStack> {
        ffi::init();

        let bio = unsafe { cvt_p(ffi::BIO_new(ffi::BIO_s_mem()))? };
        Ok(MemBio(bio))
    }
