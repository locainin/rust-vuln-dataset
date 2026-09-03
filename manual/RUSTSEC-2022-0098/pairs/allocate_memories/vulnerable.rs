    fn allocate_memories(
        &self,
        instance_index: usize,
        runtime_info: &dyn ModuleRuntimeInfo,
        store: Option<*mut dyn Store>,
        memories: &mut PrimaryMap<DefinedMemoryIndex, Memory>,
    ) -> Result<(), InstantiationError> {
        let module = runtime_info.module();

        self.validate_memory_plans(module)
            .map_err(InstantiationError::Resource)?;

        for (memory_index, plan) in module
            .memory_plans
            .iter()
            .skip(module.num_imported_memories)
        {
            let defined_index = module
                .defined_memory_index(memory_index)
                .expect("should be a defined memory since we skipped imported ones");

            let memory = unsafe {
                std::slice::from_raw_parts_mut(
                    self.memories.get_base(instance_index, defined_index),
                    self.memories.max_memory_size,
                )
            };

            if let Some(image) = runtime_info
                .memory_image(defined_index)
                .map_err(|err| InstantiationError::Resource(err.into()))?
            {
                let mut slot = self
                    .memories
                    .take_memory_image_slot(instance_index, defined_index);
                let initial_size = plan.memory.minimum * WASM_PAGE_SIZE as u64;

                // If instantiation fails, we can propagate the error
                // upward and drop the slot. This will cause the Drop
                // handler to attempt to map the range with PROT_NONE
                // memory, to reserve the space while releasing any
                // stale mappings. The next use of this slot will then
                // create a new slot that will try to map over
                // this, returning errors as well if the mapping
                // errors persist. The unmap-on-drop is best effort;
                // if it fails, then we can still soundly continue
                // using the rest of the pool and allowing the rest of
                // the process to continue, because we never perform a
                // mmap that would leave an open space for someone
                // else to come in and map something.
                slot.instantiate(initial_size as usize, Some(image))
                    .map_err(|e| InstantiationError::Resource(e.into()))?;

                memories.push(
                    Memory::new_static(plan, memory, None, Some(slot), unsafe {
                        &mut *store.unwrap()
                    })
                    .map_err(InstantiationError::Resource)?,
                );
            } else {
                memories.push(
                    Memory::new_static(plan, memory, Some(commit_memory_pages), None, unsafe {
                        &mut *store.unwrap()
                    })
                    .map_err(InstantiationError::Resource)?,
                );
            }
        }

        Ok(())
    }
