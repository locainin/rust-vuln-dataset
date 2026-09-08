    pub fn get_export(&mut self, name: &str) -> Option<Extern> {
        // All instances created have a `host_state` with a pointer pointing
        // back to themselves. If this caller doesn't have that `host_state`
        // then it probably means it was a host-created object like `Func::new`
        // which doesn't have any exports we want to return anyway.
        match self
            .caller
            .host_state()
            .downcast_ref::<Instance>()?
            .get_export(&mut self.store, name)?
        {
            Extern::Func(f) => Some(Extern::Func(f)),
            Extern::Memory(f) => Some(Extern::Memory(f)),
            // Intentionally ignore other Extern items here since this API is
            // supposed to be a temporary stop-gap until interface types.
            _ => None,
        }
    }
