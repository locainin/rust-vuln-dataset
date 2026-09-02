    fn new(instance_limits: &InstanceLimits, tunables: &Tunables) -> Result<Self> {
        // The maximum module memory page count cannot exceed 65536 pages
        if instance_limits.memory_pages > 0x10000 {
            bail!(
                "module memory page limit of {} exceeds the maximum of 65536",
                instance_limits.memory_pages
            );
        }

        // The maximum module memory page count cannot exceed the memory reservation size
        if u64::from(instance_limits.memory_pages) > tunables.static_memory_bound {
            bail!(
                "module memory page limit of {} pages exceeds maximum static memory limit of {} pages",
                instance_limits.memory_pages,
                tunables.static_memory_bound,
            );
        }

        let static_memory_bound =
            u64::from(tunables.static_memory_bound) * u64::from(WASM_PAGE_SIZE);
        let memory_size =
            usize::try_from(static_memory_bound + tunables.static_memory_offset_guard_size)
                .map_err(|_| anyhow!("memory reservation size exceeds addressable memory"))?;

        assert!(
            memory_size % crate::page_size() == 0,
            "memory size {} is not a multiple of system page size",
            memory_size
        );

        let max_instances = instance_limits.count as usize;
        let max_memories = instance_limits.memories as usize;
        let initial_memory_offset = if tunables.guard_before_linear_memory {
            usize::try_from(tunables.static_memory_offset_guard_size).unwrap()
        } else {
            0
        };

        // The entire allocation here is the size of each memory times the
        // max memories per instance times the number of instances allowed in
        // this pool, plus guard regions.
        //
        // Note, though, that guard regions are required to be after each linear
        // memory. If the `guard_before_linear_memory` setting is specified,
        // then due to the contiguous layout of linear memories the guard pages
        // after one memory are also guard pages preceding the next linear
        // memory. This means that we only need to handle pre-guard-page sizes
        // specially for the first linear memory, hence the
        // `initial_memory_offset` variable here. If guards aren't specified
        // before linear memories this is set to `0`, otherwise it's set to
        // the same size as guard regions for other memories.
        let allocation_size = memory_size
            .checked_mul(max_memories)
            .and_then(|c| c.checked_mul(max_instances))
            .and_then(|c| c.checked_add(initial_memory_offset))
            .ok_or_else(|| {
                anyhow!("total size of memory reservation exceeds addressable memory")
            })?;

        // Create a completely inaccessible region to start
        let mapping = Mmap::accessible_reserved(0, allocation_size)
            .context("failed to create memory pool mapping")?;

        let num_image_slots = if cfg!(memory_init_cow) {
            max_instances * max_memories
        } else {
            0
        };
        let image_slots: Vec<_> = std::iter::repeat_with(|| Mutex::new(None))
            .take(num_image_slots)
            .collect();

        let pool = Self {
            mapping,
            image_slots,
            memory_reservation_size: memory_size,
            initial_memory_offset,
            max_memories,
            max_instances,
            max_memory_size: (instance_limits.memory_pages as usize) * (WASM_PAGE_SIZE as usize),
            static_memory_bound,
        };

        Ok(pool)
    }
