    fn parse(s: &synstructure::Structure<'_>) -> Self {
        let mut result = Self::default();

        for v in s.variants().iter() {
            for attr in v.ast().attrs.iter() {
                result.parse_attr(attr);
            }
        }

        result
    }
