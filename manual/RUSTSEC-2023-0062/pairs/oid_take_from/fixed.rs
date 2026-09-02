    pub fn take_from<S: Source>(
        constructed: &mut Constructed<S>
    ) -> Result<Self, DecodeError<S::Error>> {
        constructed.take_primitive_if(Tag::OID, Self::from_primitive)
    }
