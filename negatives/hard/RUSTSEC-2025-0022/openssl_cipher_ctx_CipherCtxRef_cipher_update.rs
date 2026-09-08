    #[corresponds(EVP_CipherUpdate)]
    pub fn cipher_update(
        &mut self,
        input: &[u8],
        output: Option<&mut [u8]>,
    ) -> Result<usize, ErrorStack> {
        if let Some(output) = &output {
            let mut block_size = self.block_size();
            if block_size == 1 {
                block_size = 0;
            }
            let min_output_size = input.len() + block_size;
            assert!(
                output.len() >= min_output_size,
                "Output buffer size should be at least {} bytes.",
                min_output_size
            );
        }

        unsafe { self.cipher_update_unchecked(input, output) }
    }
