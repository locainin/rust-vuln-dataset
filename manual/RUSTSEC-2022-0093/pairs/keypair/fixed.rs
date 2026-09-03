#[derive(Debug)]
pub struct Keypair {
    /// The secret half of this keypair.
    pub(crate) secret: SecretKey,
    /// The public half of this keypair.
    pub(crate) public: PublicKey,
}
