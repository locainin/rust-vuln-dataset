    pub fn register(&mut self, module: &Module) {
        let compiled_module = module.compiled_module();

        // If there's not actually any functions in this module then we may
        // still need to preserve it for its data segments. Instances of this
        // module will hold a pointer to the data stored in the module itself,
        // and for schemes like uffd this performs lazy initialization which
        // could use the module in the future. For that reason we continue to
        // register empty modules and retain them.
        if compiled_module.finished_functions().len() == 0 {
            self.modules_without_code.push(compiled_module.clone());
            return;
        }

        // The module code range is exclusive for end, so make it inclusive as it
        // may be a valid PC value
        let code = compiled_module.code();
        assert!(!code.is_empty());
        let start = code.as_ptr() as usize;
        let end = start + code.len() - 1;

        // Ensure the module isn't already present in the registry
        // This is expected when a module is instantiated multiple times in the
        // same store
        if let Some(m) = self.modules_with_code.get(&end) {
            assert_eq!(m.start, start);
            return;
        }

        // Assert that this module's code doesn't collide with any other registered modules
        if let Some((_, prev)) = self.modules_with_code.range(end..).next() {
            assert!(prev.start > end);
        }

        if let Some((prev_end, _)) = self.modules_with_code.range(..=start).next_back() {
            assert!(*prev_end < start);
        }

        let prev = self.modules_with_code.insert(
            end,
            Arc::new(RegisteredModule {
                start,
                module: compiled_module.clone(),
                signatures: module.signatures().clone(),
            }),
        );
        assert!(prev.is_none());

        GLOBAL_MODULES.write().unwrap().register(start, end, module);
    }
