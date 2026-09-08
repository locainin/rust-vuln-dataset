    unsafe fn register_trampoline(&self, store: &mut StoreOpaque) {
        // This assert is required to ensure that we can indeed safely insert
        // `self` into the `store` provided, otherwise the type information we
        // have listed won't e correct. This is possible to hit with the public
        // API of Wasmtime, and should be documented in relevant functions.
        assert!(
            Engine::same(&self.engine, store.engine()),
            "cannot use a store with a different engine than a linker was created with",
        );
        let idx = self.export.anyfunc.as_ref().type_index;
        store.register_host_trampoline(idx, self.trampoline);
    }
