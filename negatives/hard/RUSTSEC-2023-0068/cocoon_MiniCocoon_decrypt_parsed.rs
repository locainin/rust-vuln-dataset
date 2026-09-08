    fn decrypt_parsed(
        &self,
        data: &mut [u8],
        detached_prefix: &MiniFormatPrefix,
    ) -> Result<(), Error> {
        let mut nonce = [0u8; 12];

        let header = detached_prefix.header();

        if data.len() < header.data_length() {
            return Err(Error::TooShort);
        }

        let data = &mut data[..header.data_length()];

        nonce.copy_from_slice(header.nonce());

        let nonce = GenericArray::from_slice(&nonce);
        let master_key = GenericArray::clone_from_slice(self.key.as_ref());
        let tag = GenericArray::from_slice(detached_prefix.tag());

        match self.config.cipher() {
            CocoonCipher::Chacha20Poly1305 => {
                let cipher = ChaCha20Poly1305::new(&master_key);
                cipher.decrypt_in_place_detached(nonce, detached_prefix.prefix(), data, tag)
            }
            CocoonCipher::Aes256Gcm => {
                let cipher = Aes256Gcm::new(&master_key);
                cipher.decrypt_in_place_detached(nonce, detached_prefix.prefix(), data, tag)
            }
        }
        .map_err(|_| Error::Cryptography)?;

        Ok(())
    }
