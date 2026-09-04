    pub unsafe fn new(data: &'static [&'static str]) -> Result<Pixmap, FltkError> {
        let mut v: Vec<*const raw::c_char> = vec![];
        for &elem in data {
            v.push(CString::safe_new(elem).into_raw());
        }
        let ptr = Fl_Pixmap_new(Box::leak(Box::new(v)).as_ptr());
        assert!(!ptr.is_null());
        if Fl_Pixmap_fail(ptr) < 0 {
            Err(FltkError::Internal(FltkErrorKind::ImageFormatError))
        } else {
            Ok(Pixmap {
                _inner: ptr,
                _refcount: AtomicUsize::new(1),
            })
        }
    }
