    pub fn try_from_arc<U, E, F>(arc: &Arc<U>, project: F) -> Result<Self, E>
    where
        U: ?Sized + Sync + Send + 'static,
        T: 'static,
        F: FnOnce(&U) -> Result<&T, E>,
    {
        let projected = project(arc)?;
        // SAFETY: fn shouldn't be able to capture any local references
        // which should mean that the projection done by f is safe
        let projected = unsafe { NonNull::new_unchecked(projected as *const T as *mut T) };
        Ok(Self {
            arc: TypeErasedArc::new(arc.clone()),
            projected,
        })
    }
