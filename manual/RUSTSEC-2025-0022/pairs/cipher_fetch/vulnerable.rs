    pub fn fetch(
        ctx: Option<&LibCtxRef>,
        algorithm: &str,
        properties: Option<&str>,
    ) -> Result<Self, ErrorStack> {
        let algorithm = CString::new(algorithm).unwrap();
        let properties = properties.map(|s| CString::new(s).unwrap());

        unsafe {
            let ptr = cvt_p(ffi::EVP_CIPHER_fetch(
                ctx.map_or(ptr::null_mut(), ForeignTypeRef::as_ptr),
                algorithm.as_ptr(),
                properties.map_or(ptr::null_mut(), |s| s.as_ptr()),
            ))?;

            Ok(Cipher::from_ptr(ptr))
        }
    }
