    fn parse(s: &synstructure::Structure<'_>) -> Self {
        let mut result = Self::default();

        for attr in s.ast().attrs.iter() {
            result.parse_attr(attr, None, None);
        }
        for v in s.variants().iter() {
            // only process actual enum variants here, as we don't want to process struct attributes twice
            if v.prefix.is_some() {
                for attr in v.ast().attrs.iter() {
                    result.parse_attr(attr, Some(v), None);
                }
            }
            for binding in v.bindings().iter() {
                for attr in binding.ast().attrs.iter() {
                    result.parse_attr(attr, Some(v), Some(binding));
                }
            }
        }

        result
    }
