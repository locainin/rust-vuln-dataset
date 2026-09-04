    fn merge(&mut self, source: Node<K>, mut into: Node<K>, median: Entry<K>) -> Node<K> {
        let source_address = source.address();
        into.merge(source, median, self.memory());
        into.save(self.allocator_mut());
        self.allocator.deallocate(source_address);
        into
    }
