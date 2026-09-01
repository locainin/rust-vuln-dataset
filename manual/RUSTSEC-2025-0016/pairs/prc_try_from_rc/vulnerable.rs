    pub fn try_from_rc<U, E, F>(rc: &Rc<U>, project: F) -> Result<Self, E>
    where
        U: ?Sized,
        T: 'static,
        F: FnOnce(&U) -> Result<&T, E>,
    {
        let projected = project(rc)?;
        // SAFETY: fn shouldn't be able to capture any local references
        // which should mean that the projection done by f is safe
        let projected = unsafe { NonNull::new_unchecked(projected as *const T as *mut T) };
        Ok(Self {
            rc: TypeErasedRc::new(rc.clone()),
            projected,
        })
    }
