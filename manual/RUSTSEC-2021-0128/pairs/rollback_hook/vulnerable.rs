    #[inline]
    pub fn rollback_hook<'c, F>(&'c self, hook: Option<F>)
    where
        F: FnMut() + Send + 'c,
    {
        self.db.borrow_mut().rollback_hook(hook);
    }
