    #[inline]
    pub fn commit_hook<F>(&self, hook: Option<F>)
    where
        F: FnMut() -> bool + Send + 'static,
    {
        self.db.borrow_mut().commit_hook(hook);
    }
