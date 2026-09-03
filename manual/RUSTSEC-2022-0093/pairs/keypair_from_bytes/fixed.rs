    pub fn from_bytes(bytes: &[u8]) -> Result<Keypair, SignatureError> {
        if bytes.len() != KEYPAIR_LENGTH {
            return Err(InternalError::BytesLengthError {
                name: "Keypair",
                length: KEYPAIR_LENGTH,
            }
            .into());
        }
        let secret = SecretKey::from_bytes(&bytes[..SECRET_KEY_LENGTH])?;
        let public = PublicKey::from_bytes(&bytes[SECRET_KEY_LENGTH..])?;

        if public != (&secret).into() {
            return Err(InternalError::MismatchedKeypairError.into());
        }

        Ok(Keypair { secret, public })
    }
