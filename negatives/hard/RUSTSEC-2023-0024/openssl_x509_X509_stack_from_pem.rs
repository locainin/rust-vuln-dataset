    #[corresponds(PEM_read_bio_X509)]
    pub fn stack_from_pem(pem: &[u8]) -> Result<Vec<X509>, ErrorStack> {
        unsafe {
            ffi::init();
            let bio = MemBioSlice::new(pem)?;

            let mut certs = vec![];
            loop {
                let r =
                    ffi::PEM_read_bio_X509(bio.as_ptr(), ptr::null_mut(), None, ptr::null_mut());
                if r.is_null() {
                    let err = ffi::ERR_peek_last_error();
                    if ffi::ERR_GET_LIB(err) as X509LenTy == ffi::ERR_LIB_PEM
                        && ffi::ERR_GET_REASON(err) == ffi::PEM_R_NO_START_LINE
                    {
                        ffi::ERR_clear_error();
                        break;
                    }

                    return Err(ErrorStack::get());
                } else {
                    certs.push(X509(r));
                }
            }

            Ok(certs)
        }
    }
