    pub fn progress_handler<F>(&self, num_ops: c_int, handler: Option<F>)
    where
        F: FnMut() -> bool + Send + RefUnwindSafe + 'static,
    {
        self.db.borrow_mut().progress_handler(num_ops, handler);
    }
