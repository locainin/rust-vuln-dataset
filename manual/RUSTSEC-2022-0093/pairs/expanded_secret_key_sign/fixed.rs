    #[allow(non_snake_case)]
    pub(crate) fn sign(&self, message: &[u8], public_key: &PublicKey) -> ed25519::Signature {
        let mut h: Sha512 = Sha512::new();
        let R: CompressedEdwardsY;
        let r: Scalar;
        let s: Scalar;
        let k: Scalar;

        h.update(&self.nonce);
        h.update(&message);

        r = Scalar::from_hash(h);
        R = (&r * &constants::ED25519_BASEPOINT_TABLE).compress();

        h = Sha512::new();
        h.update(R.as_bytes());
        h.update(public_key.as_bytes());
        h.update(&message);

        k = Scalar::from_hash(h);
        s = &(&k * &self.key) + &r;

        InternalSignature { R, s }.into()
    }
