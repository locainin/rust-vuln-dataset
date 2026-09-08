    pub(crate) fn new(
        store: Store,
        identity: UserIdentityData,
        verification_machine: VerificationMachine,
        own_identity: Option<OwnUserIdentityData>,
    ) -> Self {
        match identity {
            UserIdentityData::Own(i) => {
                Self::Own(OwnUserIdentity { inner: i, verification_machine, store })
            }
            UserIdentityData::Other(i) => {
                Self::Other(UserIdentity { inner: i, own_identity, verification_machine })
            }
        }
    }
