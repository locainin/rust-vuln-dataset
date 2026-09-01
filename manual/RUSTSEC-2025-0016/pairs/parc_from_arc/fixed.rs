    pub fn from_arc<U, F>(arc: &Arc<U>, project: F) -> Self
    where
        U: ?Sized + Send + Sync + 'static,
        F: FnOnce(&U) -> &T,
        T: 'static,
    {
        let projected = project(arc);
        // SAFETY: the returned reference always converts to a non-null pointer.
        // It's safe to convert the returned reference to a pointer (and then convert it in `Deref`)
        // because the lifetime of the reference returned by `F` must be either the lifetime
        // of the local reference passed to it, or 'static
        let projected = unsafe { NonNull::new_unchecked(projected as *const T as *mut T) };
        Self {
            arc: TypeErasedArc::new(arc.clone()),
            projected,
        }
    }
