    pub fn iter_upper_bound(&self, bound: &K) -> Iter<K, V, M> {
        if self.root_addr == NULL {
            // Map is empty.
            return Iter::null(self);
        }

        let dummy_bounds = (Bound::Unbounded, Bound::Unbounded);
        // INVARIANT: all cursors point to keys greater than or equal to bound.
        let mut cursors = vec![];

        let mut node = self.load_node(self.root_addr);
        loop {
            match node.search(bound) {
                Ok(idx) | Err(idx) => {
                    match node.node_type() {
                        NodeType::Leaf => {
                            if idx == 0 {
                                // We descended into a leaf but didn't find a node less than
                                // the upper bound. Thus we unwind the cursor stack until we
                                // hit a cursor pointing to an element other than the first key,
                                // and we shift the position backward. If there is no such cursor,
                                // the bound must be <= min element, so we return an empty iterator.
                                while let Some(cursor) = cursors.pop() {
                                    match cursor {
                                        Cursor::Node {
                                            node,
                                            next: Index::Entry(n),
                                        } => {
                                            if n == 0 {
                                                debug_assert!(node.key(n) >= bound);
                                                continue;
                                            } else {
                                                debug_assert!(node.key(n - 1) < bound);
                                                cursors.push(Cursor::Node {
                                                    node,
                                                    next: Index::Entry(n - 1),
                                                });
                                                break;
                                            }
                                        }
                                        _ => panic!("BUG: unexpected cursor shape"),
                                    }
                                }
                                // If the cursors are empty, the iterator will be empty.
                                return Iter::new_in_range(self, dummy_bounds, cursors);
                            }
                            debug_assert!(node.key(idx - 1) < bound);

                            cursors.push(Cursor::Node {
                                node,
                                next: Index::Entry(idx - 1),
                            });
                            return Iter::new_in_range(self, dummy_bounds, cursors);
                        }
                        NodeType::Internal => {
                            let child = self.load_node(node.child(idx));
                            // We push the node even if idx == node.entries_len()
                            // If we find the position in the child, the iterator will skip this
                            // cursor. But if the all keys in the child are greater than or equal to
                            // the bound, we will be able to use this cursor as a fallback.
                            cursors.push(Cursor::Node {
                                node,
                                next: Index::Entry(idx),
                            });
                            node = child;
                        }
                    }
                }
            }
        }
    }
