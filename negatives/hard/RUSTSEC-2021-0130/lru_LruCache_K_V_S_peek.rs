    pub fn peek<'a, Q>(&'a self, k: &Q) -> Option<&'a V>
    where
        KeyRef<K>: Borrow<Q>,
        Q: Hash + Eq + ?Sized,
    {
        self.map
            .get(k)
            .map(|node| unsafe { &(*(*node).val.as_ptr()) as &V })
    }
