    pub fn take_opt_from<S: Source>(
        constructed: &mut Constructed<S>
    ) -> Result<Option<Self>, DecodeError<S::Error>> {
        constructed.take_opt_primitive_if(Tag::OID, Self::from_primitive)
    }
