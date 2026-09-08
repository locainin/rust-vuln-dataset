    fn allocate(&self) -> Result<wasmtime_fiber::FiberStack, FiberStackError> {
        if self.stack_size == 0 {
            return Err(FiberStackError::NotSupported);
        }

        let index = {
            let mut alloc = self.index_allocator.lock().unwrap();
            if alloc.is_empty() {
                return Err(FiberStackError::Limit(self.max_instances as u32));
            }
            alloc.alloc(None).index()
        };

        assert!(index < self.max_instances);

        unsafe {
            // Remove the guard page from the size
            let size_without_guard = self.stack_size - self.page_size;

            let bottom_of_stack = self
                .mapping
                .as_mut_ptr()
                .add((index * self.stack_size) + self.page_size);

            commit_stack_pages(bottom_of_stack, size_without_guard)
                .map_err(FiberStackError::Resource)?;

            wasmtime_fiber::FiberStack::from_top_ptr(bottom_of_stack.add(size_without_guard))
                .map_err(|e| FiberStackError::Resource(e.into()))
        }
    }
