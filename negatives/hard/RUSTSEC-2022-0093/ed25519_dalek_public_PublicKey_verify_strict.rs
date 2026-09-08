    #[allow(non_snake_case)]
    pub fn verify_strict(
        &self,
        message: &[u8],
        signature: &ed25519::Signature,
    ) -> Result<(), SignatureError>
    {
        let signature = InternalSignature::try_from(signature)?;

        let mut h: Sha512 = Sha512::new();
        let R: EdwardsPoint;
        let k: Scalar;
        let minus_A: EdwardsPoint = -self.1;
        let signature_R: EdwardsPoint;

        match signature.R.decompress() {
            None => return Err(InternalError::VerifyError.into()),
            Some(x) => signature_R = x,
        }

        // Logical OR is fine here as we're not trying to be constant time.
        if signature_R.is_small_order() || self.1.is_small_order() {
            return Err(InternalError::VerifyError.into());
        }

        h.update(signature.R.as_bytes());
        h.update(self.as_bytes());
        h.update(&message);

        k = Scalar::from_hash(h);
        R = EdwardsPoint::vartime_double_scalar_mul_basepoint(&k, &(minus_A), &signature.s);

        if R == signature_R {
            Ok(())
        } else {
            Err(InternalError::VerifyError.into())
        }
    }
