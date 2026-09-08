    pub(crate) fn memory_grow(
        &mut self,
        index: MemoryIndex,
        delta: u64,
    ) -> Result<Option<usize>, Error> {
        match self.module().defined_memory_index(index) {
            Some(idx) => self.defined_memory_grow(idx, delta),
            None => {
                let import = self.imported_memory(index);
                unsafe {
                    Instance::from_vmctx(import.vmctx, |i| {
                        i.defined_memory_grow(import.index, delta)
                    })
                }
            }
        }
    }
