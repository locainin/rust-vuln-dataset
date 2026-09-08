    fn new(instance_limits: &InstanceLimits) -> Result<Self> {
        let page_size = crate::page_size();

        let table_size = round_up_to_pow2(
            mem::size_of::<*mut u8>()
                .checked_mul(instance_limits.table_elements as usize)
                .ok_or_else(|| anyhow!("table size exceeds addressable memory"))?,
            page_size,
        );

        let max_instances = instance_limits.count as usize;
        let max_tables = instance_limits.tables as usize;

        let allocation_size = table_size
            .checked_mul(max_tables)
            .and_then(|c| c.checked_mul(max_instances))
            .ok_or_else(|| anyhow!("total size of instance tables exceeds addressable memory"))?;

        let mapping = Mmap::accessible_reserved(allocation_size, allocation_size)
            .context("failed to create table pool mapping")?;

        Ok(Self {
            mapping,
            table_size,
            max_tables,
            max_instances,
            page_size,
            max_elements: instance_limits.table_elements,
        })
    }
