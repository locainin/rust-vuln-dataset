    pub fn to_string(self, py: Python<'_>) -> PyResult<Cow<'a, str>> {
        use std::ffi::CStr;
        match self {
            Self::Ucs1(data) => match str::from_utf8(data) {
                Ok(s) => Ok(Cow::Borrowed(s)),
                Err(e) => Err(PyUnicodeDecodeError::new_utf8(py, data, e)?.into()),
            },
            Self::Ucs2(data) => match String::from_utf16(data) {
                Ok(s) => Ok(Cow::Owned(s)),
                Err(e) => {
                    let mut message = e.to_string().as_bytes().to_vec();
                    message.push(0);

                    Err(PyUnicodeDecodeError::new(
                        py,
                        ffi::c_str!("utf-16"),
                        self.as_bytes(),
                        0..self.as_bytes().len(),
                        CStr::from_bytes_with_nul(&message).unwrap(),
                    )?
                    .into())
                }
            },
            Self::Ucs4(data) => match data.iter().map(|&c| std::char::from_u32(c)).collect() {
                Some(s) => Ok(Cow::Owned(s)),
                None => Err(PyUnicodeDecodeError::new(
                    py,
                    ffi::c_str!("utf-32"),
                    self.as_bytes(),
                    0..self.as_bytes().len(),
                    ffi::c_str!("error converting utf-32"),
                )?
                .into()),
            },
        }
    }
