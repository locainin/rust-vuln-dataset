    fn sinkable_atomic_load(&mut self, val: Value) -> Option<SinkableAtomicLoad> {
        let input = self.lower_ctx.get_value_as_source_or_const(val);
        if let InputSourceInst::UniqueUse(atomic_load, 0) = input.inst {
            if self.lower_ctx.data(atomic_load).opcode() == Opcode::AtomicLoad {
                let atomic_addr = self.lower_ctx.input_as_value(atomic_load, 0);
                return Some(SinkableAtomicLoad {
                    atomic_load,
                    atomic_addr,
                });
            }
        }
        None
    }
