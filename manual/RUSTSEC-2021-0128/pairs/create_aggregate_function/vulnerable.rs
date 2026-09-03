    #[inline]
    pub fn create_aggregate_function<A, D, T>(
        &self,
        fn_name: &str,
        n_arg: c_int,
        flags: FunctionFlags,
        aggr: D,
    ) -> Result<()>
    where
        A: RefUnwindSafe + UnwindSafe,
        D: Aggregate<A, T>,
        T: ToSql,
    {
        self.db
            .borrow_mut()
            .create_aggregate_function(fn_name, n_arg, flags, aggr)
    }
