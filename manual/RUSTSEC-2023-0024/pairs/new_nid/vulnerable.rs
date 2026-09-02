    pub fn new_nid(
        conf: Option<&ConfRef>,
        context: Option<&X509v3Context<'_>>,
        name: Nid,
        value: &str,
    ) -> Result<X509Extension, ErrorStack> {
        let value = CString::new(value).unwrap();
        unsafe {
            ffi::init();
            let conf = conf.map_or(ptr::null_mut(), ConfRef::as_ptr);
            let context = context.map_or(ptr::null_mut(), X509v3Context::as_ptr);
            let name = name.as_raw();
            let value = value.as_ptr() as *mut _;

            cvt_p(ffi::X509V3_EXT_nconf_nid(conf, context, name, value)).map(X509Extension)
        }
    }
