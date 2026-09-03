    #[inline]
    pub fn create_collation<C>(&self, collation_name: &str, x_compare: C) -> Result<()>
    where
        C: Fn(&str, &str) -> Ordering + Send + UnwindSafe + 'static,
    {
        self.db
            .borrow_mut()
            .create_collation(collation_name, x_compare)
    }
