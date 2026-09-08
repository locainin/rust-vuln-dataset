    pub fn position<F: Fn(&T) -> bool>(&self, func: F) -> Option<Idx> {
        for (inner, value) in self.values.iter() {
            if func(value) {
                return Some(Idx {
                    inner: Arc::clone(&inner),
                });
            }
        }

        None
    }
