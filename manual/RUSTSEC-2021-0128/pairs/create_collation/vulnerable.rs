    #[inline]
    pub fn create_collation<'c, C>(&'c self, collation_name: &str, x_compare: C) -> Result<()>
    where
        C: Fn(&str, &str) -> Ordering + Send + UnwindSafe + 'c,
    {
        self.db
            .borrow_mut()
            .create_collation(collation_name, x_compare)
    }
