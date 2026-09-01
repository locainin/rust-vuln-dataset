    pub fn project<U, F>(&self, project: F) -> Parc<U>
    where
        T: Send + Sync,
        U: ?Sized + 'static,
        F: FnOnce(&T) -> &U,
    {
        let projected = project(self);
        // SAFETY: the returned reference always converts to a non-null pointer.
        // It's safe to convert the returned reference to a pointer (and then convert it in `Deref`)
        // because the lifetime of the reference returned by `F` must be either the lifetime
        // of the local reference passed to it, or 'static
        let projected = unsafe { NonNull::new_unchecked(projected as *const U as *mut U) };
        Parc::<U> {
            arc: self.arc.clone(),
            projected,
        }
    }
