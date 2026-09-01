    pub fn from_rc<U, F>(rc: &Rc<U>, project: F) -> Self
    where
        U: ?Sized,
        T: 'static,
        F: FnOnce(&U) -> &T,
    {
        let projected = project(rc);
        // SAFETY: fn shouldn't be able to capture any local references
        // which should mean that the projection done by f is safe
        let projected = unsafe { NonNull::new_unchecked(projected as *const T as *mut T) };
        Self {
            rc: TypeErasedRc::new(rc.clone()),
            projected,
        }
    }
