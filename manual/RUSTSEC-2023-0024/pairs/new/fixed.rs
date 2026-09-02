    pub fn new(
        conf: Option<&ConfRef>,
        context: Option<&X509v3Context<'_>>,
        name: &str,
        value: &str,
    ) -> Result<X509Extension, ErrorStack> {
        let name = CString::new(name).unwrap();
        let value = CString::new(value).unwrap();
        let mut ctx;
        unsafe {
            ffi::init();
            let conf = conf.map_or(ptr::null_mut(), ConfRef::as_ptr);
            let context_ptr = match context {
                Some(c) => c.as_ptr(),
                None => {
                    ctx = mem::zeroed();

                    ffi::X509V3_set_ctx(
                        &mut ctx,
                        ptr::null_mut(),
                        ptr::null_mut(),
                        ptr::null_mut(),
                        ptr::null_mut(),
                        0,
                    );
                    &mut ctx
                }
            };
            let name = name.as_ptr() as *mut _;
            let value = value.as_ptr() as *mut _;

            cvt_p(ffi::X509V3_EXT_nconf(conf, context_ptr, name, value)).map(X509Extension)
        }
    }
