    pub fn new(
        conf: Option<&ConfRef>,
        context: Option<&X509v3Context<'_>>,
        name: &str,
        value: &str,
    ) -> Result<X509Extension, ErrorStack> {
        let name = CString::new(name).unwrap();
        let value = CString::new(value).unwrap();
        unsafe {
            ffi::init();
            let conf = conf.map_or(ptr::null_mut(), ConfRef::as_ptr);
            let context = context.map_or(ptr::null_mut(), X509v3Context::as_ptr);
            let name = name.as_ptr() as *mut _;
            let value = value.as_ptr() as *mut _;

            cvt_p(ffi::X509V3_EXT_nconf(conf, context, name, value)).map(X509Extension)
        }
    }
