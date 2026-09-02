    pub fn decrypt_ad(
        &mut self,
        authtext: &[u8],
        ciphertext: &[u8],
        out: &mut [u8],
    ) -> Result<usize, Error> {
        if (ciphertext.len() < TAGLEN) || out.len() < (ciphertext.len() - TAGLEN) {
            return Err(Error::Decrypt);
        }

        if !self.has_key {
            return Err(StateProblem::MissingKeyMaterial.into());
        }

        validate_nonce(self.n)?;
        let len = self.cipher.decrypt(self.n, authtext, ciphertext, out)?;

        // We have validated this will not wrap around.
        self.n += 1;

        Ok(len)
    }
