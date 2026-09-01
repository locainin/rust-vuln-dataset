    pub fn project<U, F>(&self, project: F) -> Prc<U>
    where
        U: ?Sized + 'static,
        F: FnOnce(&T) -> &U,
    {
        let projected = project(self);
        // SAFETY: fn shouldn't be able to capture any local references
        // which should mean that the projection done by f is safe
        let projected = unsafe { NonNull::new_unchecked(projected as *const U as *mut U) };
        Prc::<U> {
            rc: self.rc.clone(),
            projected,
        }
    }
