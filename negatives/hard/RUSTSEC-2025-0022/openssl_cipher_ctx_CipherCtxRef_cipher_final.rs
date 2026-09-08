    #[corresponds(EVP_CipherFinal)]
    pub fn cipher_final(&mut self, output: &mut [u8]) -> Result<usize, ErrorStack> {
        let block_size = self.block_size();
        if block_size > 1 {
            assert!(output.len() >= block_size);
        }

        unsafe { self.cipher_final_unchecked(output) }
    }
