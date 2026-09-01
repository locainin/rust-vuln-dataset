    fn skip_group(&mut self) -> crate::Result<()> {
        self.incr_recursion()?;
        let ret = self.skip_group_no_depth_check();
        self.decr_recursion();
        ret
    }
