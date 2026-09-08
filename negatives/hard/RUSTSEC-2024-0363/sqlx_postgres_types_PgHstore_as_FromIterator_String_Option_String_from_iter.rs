    fn from_iter<T: IntoIterator<Item = (String, Option<String>)>>(iter: T) -> Self {
        let mut result = Self::default();

        for (key, value) in iter {
            result.0.insert(key, value);
        }

        result
    }
