    pub fn range(&self, key_range: impl RangeBounds<K>) -> Iter<K, V, M> {
        if self.root_addr == NULL {
            // Map is empty.
            return Iter::null(self);
        }

        let range = (
            key_range.start_bound().cloned(),
            key_range.end_bound().cloned(),
        );

        let mut cursors = vec![];

        match key_range.start_bound() {
            Bound::Unbounded => {
                cursors.push(Cursor::Address(self.root_addr));
                Iter::new_in_range(self, range, cursors)
            }
            Bound::Included(key) | Bound::Excluded(key) => {
                let mut node = self.load_node(self.root_addr);
                loop {
                    match node.search(key) {
                        Ok(idx) => {
                            if let Bound::Included(_) = key_range.start_bound() {
                                // We found the key exactly matching the left bound.
                                // Here is where we'll start the iteration.
                                cursors.push(Cursor::Node {
                                    node,
                                    next: Index::Entry(idx),
                                });
                                return Iter::new_in_range(self, range, cursors);
                            } else {
                                // We found the key that we must
                                // exclude.  We add its right neighbor
                                // to the stack and start iterating
                                // from its right child.
                                let right_child = match node.node_type() {
                                    NodeType::Internal => Some(node.child(idx + 1)),
                                    NodeType::Leaf => None,
                                };

                                if idx + 1 != node.entries_len()
                                    && key_range.contains(node.key(idx + 1))
                                {
                                    cursors.push(Cursor::Node {
                                        node,
                                        next: Index::Entry(idx + 1),
                                    });
                                }
                                if let Some(right_child) = right_child {
                                    cursors.push(Cursor::Address(right_child));
                                }
                                return Iter::new_in_range(self, range, cursors);
                            }
                        }
                        Err(idx) => {
                            // The `idx` variable points to the first
                            // key that is greater than the left
                            // bound.
                            //
                            // If the index points to a valid node, we
                            // will visit its left subtree and then
                            // return to this key.
                            //
                            // If the index points at the end of
                            // array, we'll continue with the right
                            // child of the last key.

                            // Load the left child of the node to visit if it exists.
                            // This is done first to avoid cloning the node.
                            let child = match node.node_type() {
                                NodeType::Internal => {
                                    // Note that loading a child node cannot fail since
                                    // len(children) = len(entries) + 1
                                    Some(self.load_node(node.child(idx)))
                                }
                                NodeType::Leaf => None,
                            };

                            if idx < node.entries_len() && key_range.contains(node.key(idx)) {
                                cursors.push(Cursor::Node {
                                    node,
                                    next: Index::Entry(idx),
                                });
                            }

                            match child {
                                None => {
                                    // Leaf node. Return an iterator with the found cursors.
                                    return Iter::new_in_range(self, range, cursors);
                                }
                                Some(child) => {
                                    // Iterate over the child node.
                                    node = child;
                                }
                            }
                        }
                    }
                }
            }
        }
    }
