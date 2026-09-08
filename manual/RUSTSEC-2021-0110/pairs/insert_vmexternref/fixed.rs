    pub unsafe fn insert_vmexternref_without_gc(&mut self, r: VMExternRef) {
        self.externref_activations_table.insert_without_gc(r);
    }
