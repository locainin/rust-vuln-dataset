    fn _retain(&self, mut f: impl FnMut(&K, &mut V) -> bool) {
        self.shards
            .iter()
            .for_each(|s| s.write().retain(|k, v| f(k, v.get_mut())));
    }
