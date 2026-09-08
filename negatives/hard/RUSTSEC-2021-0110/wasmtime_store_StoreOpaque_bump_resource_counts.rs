    pub fn bump_resource_counts(&mut self, module: &Module) -> Result<()> {
        fn bump(slot: &mut usize, max: usize, amt: usize, desc: &str) -> Result<()> {
            let new = slot.saturating_add(amt);
            if new > max {
                bail!(
                    "resource limit exceeded: {} count too high at {}",
                    desc,
                    new
                );
            }
            *slot = new;
            Ok(())
        }

        let module = module.env_module();
        let memories = module.memory_plans.len() - module.num_imported_memories;
        let tables = module.table_plans.len() - module.num_imported_tables;

        bump(&mut self.instance_count, self.instance_limit, 1, "instance")?;
        bump(
            &mut self.memory_count,
            self.memory_limit,
            memories,
            "memory",
        )?;
        bump(&mut self.table_count, self.table_limit, tables, "table")?;

        Ok(())
    }
