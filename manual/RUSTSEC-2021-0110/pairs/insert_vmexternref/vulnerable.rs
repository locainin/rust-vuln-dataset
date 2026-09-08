    pub unsafe fn insert_vmexternref(&mut self, r: VMExternRef) {
        self.externref_activations_table
            .insert_with_gc(r, &self.modules)
    }
