    #[cfg(feature = "window")]
    #[cfg_attr(docsrs, doc(cfg(feature = "window")))]
    #[inline]
    pub fn create_window_function<A, W, T>(
        &self,
        fn_name: &str,
        n_arg: c_int,
        flags: FunctionFlags,
        aggr: W,
    ) -> Result<()>
    where
        A: RefUnwindSafe + UnwindSafe,
        W: WindowAggregate<A, T>,
        T: ToSql,
    {
        self.db
            .borrow_mut()
            .create_window_function(fn_name, n_arg, flags, aggr)
    }
