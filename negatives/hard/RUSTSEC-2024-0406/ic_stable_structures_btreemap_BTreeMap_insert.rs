    pub fn insert(&mut self, key: K, value: V) -> Option<V> {
        let value = value.to_bytes_checked().to_vec();

        let root = if self.root_addr == NULL {
            // No root present. Allocate one.
            let node = self.allocate_node(NodeType::Leaf);
            self.root_addr = node.address();
            self.save();
            node
        } else {
            // Load the root from memory.
            let mut root = self.load_node(self.root_addr);

            // Check if the key already exists in the root.
            if let Ok(idx) = root.search(&key) {
                // The key exists. Overwrite it and return the previous value.
                let (_, previous_value) = root.swap_entry(idx, (key, value), self.memory());
                root.save(self.allocator_mut());
                return Some(V::from_bytes(Cow::Owned(previous_value)));
            }

            // If the root is full, we need to introduce a new node as the root.
            //
            // NOTE: In the case where we are overwriting an existing key, then introducing
            // a new root node isn't strictly necessary. However, that's a micro-optimization
            // that adds more complexity than it's worth.
            if root.is_full() {
                // The root is full. Allocate a new node that will be used as the new root.
                let mut new_root = self.allocate_node(NodeType::Internal);

                // The new root has the old root as its only child.
                new_root.push_child(self.root_addr);

                // Update the root address.
                self.root_addr = new_root.address();
                self.save();

                // Split the old (full) root.
                self.split_child(&mut new_root, 0);

                new_root
            } else {
                root
            }
        };

        self.insert_nonfull(root, key, value)
            .map(Cow::Owned)
            .map(V::from_bytes)
    }
