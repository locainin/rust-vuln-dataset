    pub fn limiter(
        &mut self,
        mut limiter: impl FnMut(&mut T) -> &mut (dyn crate::ResourceLimiter) + Send + Sync + 'static,
    ) {
        // Apply the limits on instances, tables, and memory given by the limiter:
        let inner = &mut self.inner;
        let (instance_limit, table_limit, memory_limit) = {
            let l = limiter(&mut inner.data);
            (l.instances(), l.tables(), l.memories())
        };
        let innermost = &mut inner.inner;
        innermost.instance_limit = instance_limit;
        innermost.table_limit = table_limit;
        innermost.memory_limit = memory_limit;

        // Save the limiter accessor function:
        inner.limiter = Some(Box::new(limiter));
    }
