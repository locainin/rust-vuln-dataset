    pub(crate) fn table_init(
        &mut self,
        table_index: TableIndex,
        elem_index: ElemIndex,
        dst: u32,
        src: u32,
        len: u32,
    ) -> Result<(), Trap> {
        // TODO: this `clone()` shouldn't be necessary but is used for now to
        // inform `rustc` that the lifetime of the elements here are
        // disconnected from the lifetime of `self`.
        let module = self.module().clone();

        let empty = TableSegmentElements::Functions(Box::new([]));
        let elements = match module.passive_elements_map.get(&elem_index) {
            Some(index) if !self.dropped_elements.contains(elem_index) => {
                &module.passive_elements[*index]
            }
            _ => &empty,
        };
        self.table_init_segment(table_index, elements, dst, src, len)
    }
