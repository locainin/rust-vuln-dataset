    #[inline]
    pub fn rollback_hook<F>(&self, hook: Option<F>)
    where
        F: FnMut() + Send + 'static,
    {
        self.db.borrow_mut().rollback_hook(hook);
    }
