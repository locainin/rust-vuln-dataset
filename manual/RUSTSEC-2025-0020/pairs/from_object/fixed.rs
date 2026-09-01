    pub fn from_object<'py>(
        src: &Bound<'py, PyAny>,
        encoding: &str,
        errors: &str,
    ) -> PyResult<Bound<'py, PyString>> {
        let encoding = CString::new(encoding)?;
        let errors = CString::new(errors)?;
        unsafe {
            ffi::PyUnicode_FromEncodedObject(
                src.as_ptr(),
                encoding.as_ptr().cast(),
                errors.as_ptr().cast(),
            )
            .assume_owned_or_err(src.py())
            .downcast_into_unchecked()
        }
    }
