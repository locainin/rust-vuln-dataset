    #[allow(non_snake_case)]
    pub(crate) fn sign_prehashed<'a, D>(
        &self,
        prehashed_message: D,
        public_key: &PublicKey,
        context: Option<&'a [u8]>,
    ) -> Result<ed25519::Signature, SignatureError>
    where
        D: Digest<OutputSize = U64>,
    {
        let mut h: Sha512;
        let mut prehash: [u8; 64] = [0u8; 64];
        let R: CompressedEdwardsY;
        let r: Scalar;
        let s: Scalar;
        let k: Scalar;

        let ctx: &[u8] = context.unwrap_or(b""); // By default, the context is an empty string.

        if ctx.len() > 255 {
            return Err(SignatureError::from(InternalError::PrehashedContextLengthError));
        }

        let ctx_len: u8 = ctx.len() as u8;

        // Get the result of the pre-hashed message.
        prehash.copy_from_slice(prehashed_message.finalize().as_slice());

        // This is the dumbest, ten-years-late, non-admission of fucking up the
        // domain separation I have ever seen.  Why am I still required to put
        // the upper half "prefix" of the hashed "secret key" in here?  Why
        // can't the user just supply their own nonce and decide for themselves
        // whether or not they want a deterministic signature scheme?  Why does
        // the message go into what's ostensibly the signature domain separation
        // hash?  Why wasn't there always a way to provide a context string?
        //
        // ...
        //
        // This is a really fucking stupid bandaid, and the damned scheme is
        // still bleeding from malleability, for fuck's sake.
        h = Sha512::new()
            .chain(b"SigEd25519 no Ed25519 collisions")
            .chain(&[1]) // Ed25519ph
            .chain(&[ctx_len])
            .chain(ctx)
            .chain(&self.nonce)
            .chain(&prehash[..]);

        r = Scalar::from_hash(h);
        R = (&r * &constants::ED25519_BASEPOINT_TABLE).compress();

        h = Sha512::new()
            .chain(b"SigEd25519 no Ed25519 collisions")
            .chain(&[1]) // Ed25519ph
            .chain(&[ctx_len])
            .chain(ctx)
            .chain(R.as_bytes())
            .chain(public_key.as_bytes())
            .chain(&prehash[..]);

        k = Scalar::from_hash(h);
        s = &(&k * &self.key) + &r;

        Ok(InternalSignature { R, s }.into())
    }
