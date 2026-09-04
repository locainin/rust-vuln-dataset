    fn merge(&mut self, source: Node<K>, mut into: Node<K>, median: Entry<K>) -> Node<K> {
        into.merge(source, median, &mut self.allocator);
        into
    }
