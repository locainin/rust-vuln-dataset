    #[inline]
    pub fn commit_hook<'c, F>(&'c self, hook: Option<F>)
    where
        F: FnMut() -> bool + Send + 'c,
    {
        self.db.borrow_mut().commit_hook(hook);
    }
