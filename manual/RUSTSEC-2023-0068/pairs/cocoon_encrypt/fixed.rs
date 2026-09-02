    pub fn encrypt(&mut self, data: &mut [u8]) -> Result<[u8; PREFIX_SIZE], Error> {
        let mut salt = [0u8; 16];
        let mut nonce = [0u8; 12];

        match self.rng {
            #[cfg(feature = "std")]
            RngVariant::Thread(ref mut rng) => {
                rng.fill_bytes(&mut salt);
                rng.fill_bytes(&mut nonce);
            }
            RngVariant::Std(ref mut rng) => {
                rng.fill_bytes(&mut salt);
                rng.fill_bytes(&mut nonce);
            }
            RngVariant::None => unreachable!(),
        }

        let header = CocoonHeader::new(self.config.clone(), salt, nonce, data.len());
        let prefix = FormatPrefix::new(header);

        let master_key = match self.config.kdf() {
            CocoonKdf::Pbkdf2 => {
                kdf::pbkdf2::derive(&salt, self.password, self.config.kdf_iterations())
            }
        };

        let nonce = GenericArray::from_slice(&nonce);
        let master_key = GenericArray::clone_from_slice(master_key.as_ref());

        let tag: [u8; 16] = match self.config.cipher() {
            CocoonCipher::Chacha20Poly1305 => {
                let cipher = ChaCha20Poly1305::new(&master_key);
                cipher.encrypt_in_place_detached(nonce, prefix.prefix(), data)
            }
            CocoonCipher::Aes256Gcm => {
                let cipher = Aes256Gcm::new(&master_key);
                cipher.encrypt_in_place_detached(nonce, prefix.prefix(), data)
            }
        }
        .map_err(|_| Error::Cryptography)?
        .into();

        Ok(prefix.serialize(&tag))
    }
