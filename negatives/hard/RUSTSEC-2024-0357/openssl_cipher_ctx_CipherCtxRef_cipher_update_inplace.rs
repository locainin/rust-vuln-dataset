    #[corresponds(EVP_CipherUpdate)]
    pub fn cipher_update_inplace(
        &mut self,
        data: &mut [u8],
        inlen: usize,
    ) -> Result<usize, ErrorStack> {
        assert!(inlen <= data.len(), "Input size may not exceed buffer size");
        let block_size = self.block_size();
        if block_size != 1 {
            assert!(
                data.len() >= inlen + block_size,
                "Output buffer size must be at least {} bytes.",
                inlen + block_size
            );
        }

        let inlen = c_int::try_from(inlen).unwrap();
        let mut outlen = 0;
        unsafe {
            cvt(ffi::EVP_CipherUpdate(
                self.as_ptr(),
                data.as_mut_ptr(),
                &mut outlen,
                data.as_ptr(),
                inlen,
            ))
        }?;

        Ok(outlen as usize)
    }
