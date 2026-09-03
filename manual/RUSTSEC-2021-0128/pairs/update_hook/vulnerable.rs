    #[inline]
    pub fn update_hook<'c, F>(&'c self, hook: Option<F>)
    where
        F: FnMut(Action, &str, &str, i64) + Send + 'c,
    {
        self.db.borrow_mut().update_hook(hook);
    }
