    unsafe fn register_trampoline(&self, store: &mut StoreOpaque) {
        let idx = self.export.anyfunc.as_ref().type_index;
        store.register_host_trampoline(idx, self.trampoline);
    }
