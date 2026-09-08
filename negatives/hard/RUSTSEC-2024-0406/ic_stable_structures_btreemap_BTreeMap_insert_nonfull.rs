    fn insert_nonfull(&mut self, mut node: Node<K>, key: K, value: Vec<u8>) -> Option<Vec<u8>> {
        // We're guaranteed by the caller that the provided node is not full.
        assert!(!node.is_full());

        // Look for the key in the node.
        match node.search(&key) {
            Ok(idx) => {
                // The key is already in the node.
                // Overwrite it and return the previous value.
                let (_, previous_value) = node.swap_entry(idx, (key, value), self.memory());

                node.save(self.allocator_mut());
                Some(previous_value)
            }
            Err(idx) => {
                // The key isn't in the node. `idx` is where that key should be inserted.

                match node.node_type() {
                    NodeType::Leaf => {
                        // The node is a non-full leaf.
                        // Insert the entry at the proper location.
                        node.insert_entry(idx, (key, value));
                        node.save(self.allocator_mut());

                        // Update the length.
                        self.length += 1;
                        self.save();

                        // No previous value to return.
                        None
                    }
                    NodeType::Internal => {
                        // The node is an internal node.
                        // Load the child that we should add the entry to.
                        let mut child = self.load_node(node.child(idx));

                        if child.is_full() {
                            // Check if the key already exists in the child.
                            if let Ok(idx) = child.search(&key) {
                                // The key exists. Overwrite it and return the previous value.
                                let (_, previous_value) =
                                    child.swap_entry(idx, (key, value), self.memory());
                                child.save(self.allocator_mut());
                                return Some(previous_value);
                            }

                            // The child is full. Split the child.
                            self.split_child(&mut node, idx);

                            // The children have now changed. Search again for
                            // the child where we need to store the entry in.
                            let idx = node.search(&key).unwrap_or_else(|idx| idx);
                            child = self.load_node(node.child(idx));
                        }

                        // The child should now be not full.
                        assert!(!child.is_full());

                        self.insert_nonfull(child, key, value)
                    }
                }
            }
        }
    }
