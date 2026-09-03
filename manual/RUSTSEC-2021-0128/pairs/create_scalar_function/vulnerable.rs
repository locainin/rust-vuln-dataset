    #[inline]
    pub fn create_scalar_function<'c, F, T>(
        &'c self,
        fn_name: &str,
        n_arg: c_int,
        flags: FunctionFlags,
        x_func: F,
    ) -> Result<()>
    where
        F: FnMut(&Context<'_>) -> Result<T> + Send + UnwindSafe + 'c,
        T: ToSql,
    {
        self.db
            .borrow_mut()
            .create_scalar_function(fn_name, n_arg, flags, x_func)
    }
