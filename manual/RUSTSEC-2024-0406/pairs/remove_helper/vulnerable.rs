    fn remove_helper(&mut self, mut node: Node<K>, key: &K) -> Option<Vec<u8>> {
        if node.address() != self.root_addr {
            // We're guaranteed that whenever this method is called an entry can be
            // removed from the node without it needing to be merged into a sibling.
            // This strengthened condition allows us to delete an entry in a single
            // pass most of the time without having to back up.
            assert!(node.can_remove_entry_without_merging());
        }

        match node.node_type() {
            NodeType::Leaf => {
                match node.search(key) {
                    Ok(idx) => {
                        // Case 1: The node is a leaf node and the key exists in it.
                        // This is the simplest case. The key is removed from the leaf.
                        let value = node.remove_entry(idx, self.memory()).1;
                        self.length -= 1;

                        if node.entries_len() == 0 {
                            assert_eq!(
                                node.address(), self.root_addr,
                                "Removal can only result in an empty leaf node if that node is the root"
                            );

                            // Deallocate the empty node.
                            self.allocator.deallocate(node.address());
                            self.root_addr = NULL;
                        } else {
                            node.save(self.allocator_mut());
                        }

                        self.save();
                        Some(value)
                    }
                    _ => None, // Key not found.
                }
            }
            NodeType::Internal => {
                match node.search(key) {
                    Ok(idx) => {
                        // Case 2: The node is an internal node and the key exists in it.

                        let left_child = self.load_node(node.child(idx));
                        if left_child.can_remove_entry_without_merging() {
                            // Case 2.a: A key can be removed from the left child without merging.
                            //
                            //                       parent
                            //                  [..., key, ...]
                            //                       /   \
                            //            [left child]   [...]
                            //           /            \
                            //        [...]         [..., key predecessor]
                            //
                            // In this case, we replace `key` with the key's predecessor from the
                            // left child's subtree, then we recursively delete the key's
                            // predecessor for the following end result:
                            //
                            //                       parent
                            //            [..., key predecessor, ...]
                            //                       /   \
                            //            [left child]   [...]
                            //           /            \
                            //        [...]          [...]

                            // Recursively delete the predecessor.
                            // TODO(EXC-1034): Do this in a single pass.
                            let predecessor = left_child.get_max(self.memory());
                            self.remove_helper(left_child, &predecessor.0)?;

                            // Replace the `key` with its predecessor.
                            let (_, old_value) = node.swap_entry(idx, predecessor, self.memory());

                            // Save the parent node.
                            node.save(self.allocator_mut());
                            return Some(old_value);
                        }

                        let right_child = self.load_node(node.child(idx + 1));
                        if right_child.can_remove_entry_without_merging() {
                            // Case 2.b: A key can be removed from the right child without merging.
                            //
                            //                       parent
                            //                  [..., key, ...]
                            //                       /   \
                            //                   [...]   [right child]
                            //                          /             \
                            //              [key successor, ...]     [...]
                            //
                            // In this case, we replace `key` with the key's successor from the
                            // right child's subtree, then we recursively delete the key's
                            // successor for the following end result:
                            //
                            //                       parent
                            //            [..., key successor, ...]
                            //                       /   \
                            //                  [...]   [right child]
                            //                           /            \
                            //                        [...]          [...]

                            // Recursively delete the successor.
                            // TODO(EXC-1034): Do this in a single pass.
                            let successor = right_child.get_min(self.memory());
                            self.remove_helper(right_child, &successor.0)?;

                            // Replace the `key` with its successor.
                            let (_, old_value) = node.swap_entry(idx, successor, self.memory());

                            // Save the parent node.
                            node.save(self.allocator_mut());
                            return Some(old_value);
                        }

                        // Case 2.c: Both the left and right child are at their minimum sizes.
                        //
                        //                       parent
                        //                  [..., key, ...]
                        //                       /   \
                        //            [left child]   [right child]
                        //
                        // In this case, we merge (left child, key, right child) into a single
                        // node. The result will look like this:
                        //
                        //                       parent
                        //                     [...  ...]
                        //                         |
                        //          [left child, `key`, right child] <= new child
                        //
                        // We then recurse on this new child to delete `key`.
                        //
                        // If `parent` becomes empty (which can only happen if it's the root),
                        // then `parent` is deleted and `new_child` becomes the new root.
                        assert!(left_child.at_minimum());
                        assert!(right_child.at_minimum());

                        // Merge the right child into the left child.
                        let mut new_child = self.merge(
                            right_child,
                            left_child,
                            node.remove_entry(idx, self.memory()),
                        );

                        // Remove the right child from the parent node.
                        node.remove_child(idx + 1);

                        if node.entries_len() == 0 {
                            // Can only happen if this node is root.
                            assert_eq!(node.address(), self.root_addr);
                            assert_eq!(node.child(0), new_child.address());
                            assert_eq!(node.children_len(), 1);

                            self.root_addr = new_child.address();

                            // Deallocate the root node.
                            self.allocator.deallocate(node.address());
                            self.save();
                        }

                        node.save(self.allocator_mut());
                        new_child.save(self.allocator_mut());

                        // Recursively delete the key.
                        self.remove_helper(new_child, key)
                    }
                    Err(idx) => {
                        // Case 3: The node is an internal node and the key does NOT exist in it.

                        // If the key does exist in the tree, it will exist in the subtree at index
                        // `idx`.
                        let mut child = self.load_node(node.child(idx));

                        if child.can_remove_entry_without_merging() {
                            // The child has enough nodes. Recurse to delete the `key` from the
                            // `child`.
                            return self.remove_helper(child, key);
                        }

                        // An entry can't be removed from the child without merging.
                        // See if it has a sibling where an entry can be removed without merging.
                        let mut left_sibling = if idx > 0 {
                            Some(self.load_node(node.child(idx - 1)))
                        } else {
                            None
                        };

                        let mut right_sibling = if idx + 1 < node.children_len() {
                            Some(self.load_node(node.child(idx + 1)))
                        } else {
                            None
                        };

                        if let Some(ref mut left_sibling) = left_sibling {
                            if left_sibling.can_remove_entry_without_merging() {
                                // Case 3.a (left):
                                // A key can be removed from the left child without merging.
                                //
                                //                            [d] (parent)
                                //                           /   \
                                //  (left sibling) [a, b, c]     [e, f] (child)
                                //                         \
                                //                         [c']
                                //
                                // In this case, we move a key down from the parent into the child
                                // and move a key from the left sibling up into the parent
                                // resulting in the following tree:
                                //
                                //                            [c] (parent)
                                //                           /   \
                                //       (left sibling) [a, b]   [d, e, f] (child)
                                //                              /
                                //                            [c']
                                //
                                // We then recurse to delete the key from the child.

                                // Remove the last entry from the left sibling.
                                let (left_sibling_key, left_sibling_value) =
                                    left_sibling.pop_entry(self.memory()).unwrap();

                                // Replace the parent's entry with the one from the left sibling.
                                let (parent_key, parent_value) = node.swap_entry(
                                    idx - 1,
                                    (left_sibling_key, left_sibling_value),
                                    self.memory(),
                                );

                                // Move the entry from the parent into the child.
                                child.insert_entry(0, (parent_key, parent_value));

                                // Move the last child from left sibling into child.
                                if let Some(last_child) = left_sibling.pop_child() {
                                    assert_eq!(left_sibling.node_type(), NodeType::Internal);
                                    assert_eq!(child.node_type(), NodeType::Internal);

                                    child.insert_child(0, last_child);
                                } else {
                                    assert_eq!(left_sibling.node_type(), NodeType::Leaf);
                                    assert_eq!(child.node_type(), NodeType::Leaf);
                                }

                                left_sibling.save(self.allocator_mut());
                                child.save(self.allocator_mut());
                                node.save(self.allocator_mut());
                                return self.remove_helper(child, key);
                            }
                        }

                        if let Some(right_sibling) = &mut right_sibling {
                            if right_sibling.can_remove_entry_without_merging() {
                                // Case 3.a (right):
                                // A key can be removed from the right child without merging.
                                //
                                //                            [c] (parent)
                                //                           /   \
                                //             (child) [a, b]     [d, e, f] (right sibling)
                                //                               /
                                //                            [d']
                                //
                                // In this case, we move a key down from the parent into the child
                                // and move a key from the right sibling up into the parent
                                // resulting in the following tree:
                                //
                                //                            [d] (parent)
                                //                           /   \
                                //          (child) [a, b, c]     [e, f] (right sibling)
                                //                          \
                                //                           [d']
                                //
                                // We then recurse to delete the key from the child.

                                // Remove the first entry from the right sibling.
                                let (right_sibling_key, right_sibling_value) =
                                    right_sibling.remove_entry(0, self.memory());

                                // Replace the parent's entry with the one from the right sibling.
                                let parent_entry = node.swap_entry(
                                    idx,
                                    (right_sibling_key, right_sibling_value),
                                    self.memory(),
                                );

                                // Move the entry from the parent into the child.
                                child.push_entry(parent_entry);

                                // Move the first child of right_sibling into `child`.
                                match right_sibling.node_type() {
                                    NodeType::Internal => {
                                        assert_eq!(child.node_type(), NodeType::Internal);
                                        child.push_child(right_sibling.remove_child(0));
                                    }
                                    NodeType::Leaf => {
                                        assert_eq!(child.node_type(), NodeType::Leaf);
                                    }
                                }

                                right_sibling.save(self.allocator_mut());
                                child.save(self.allocator_mut());
                                node.save(self.allocator_mut());
                                return self.remove_helper(child, key);
                            }
                        }

                        // Case 3.b: Both the left and right siblings are at their minimum sizes.

                        if let Some(left_sibling) = left_sibling {
                            // Merge child into left sibling if it exists.

                            assert!(left_sibling.at_minimum());
                            let left_sibling = self.merge(
                                child,
                                left_sibling,
                                node.remove_entry(idx - 1, self.memory()),
                            );
                            // Removing child from parent.
                            node.remove_child(idx);

                            if node.entries_len() == 0 {
                                self.allocator.deallocate(node.address());

                                if node.address() == self.root_addr {
                                    // Update the root.
                                    self.root_addr = left_sibling.address();
                                    self.save();
                                }
                            } else {
                                node.save(self.allocator_mut());
                            }

                            return self.remove_helper(left_sibling, key);
                        }

                        if let Some(right_sibling) = right_sibling {
                            // Merge child into right sibling.

                            assert!(right_sibling.at_minimum());
                            let right_sibling = self.merge(
                                child,
                                right_sibling,
                                node.remove_entry(idx, self.memory()),
                            );

                            // Removing child from parent.
                            node.remove_child(idx);

                            if node.entries_len() == 0 {
                                self.allocator.deallocate(node.address());

                                if node.address() == self.root_addr {
                                    // Update the root.
                                    self.root_addr = right_sibling.address();
                                    self.save();
                                }
                            } else {
                                node.save(self.allocator_mut());
                            }

                            return self.remove_helper(right_sibling, key);
                        }

                        unreachable!("At least one of the siblings must exist.");
                    }
                }
            }
        }
    }
