    pub fn encrypt(&mut self, data: &mut [u8]) -> Result<[u8; MINI_PREFIX_SIZE], Error> {
        let mut nonce = [0u8; 12];
        self.rng.fill_bytes(&mut nonce);

        let header = MiniCocoonHeader::new(nonce, data.len());
        let prefix = MiniFormatPrefix::new(header);

        let nonce = GenericArray::from_slice(&nonce);
        let key = GenericArray::clone_from_slice(self.key.as_ref());

        let tag: [u8; 16] = match self.config.cipher() {
            CocoonCipher::Chacha20Poly1305 => {
                let cipher = ChaCha20Poly1305::new(&key);
                cipher.encrypt_in_place_detached(nonce, prefix.prefix(), data)
            }
            CocoonCipher::Aes256Gcm => {
                let cipher = Aes256Gcm::new(&key);
                cipher.encrypt_in_place_detached(nonce, prefix.prefix(), data)
            }
        }
        .map_err(|_| Error::Cryptography)?
        .into();

        Ok(prefix.serialize(&tag))
    }
