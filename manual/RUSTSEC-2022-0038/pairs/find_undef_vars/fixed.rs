    fn find_undef_vars(
        &'a self,
        scope: &Scope<'a>,
        defined: &HashSet<&'a str>,
        unused: &mut Vec<&'a Spanning<&'a str>>,
        visited: &mut HashSet<Scope<'a>>,
    ) {
        let mut to_visit = Vec::new();
        if let Some(spreads) = self.find_undef_vars_inner(scope, defined, unused, visited) {
            to_visit.push(spreads);
        }
        while let Some(spreads) = to_visit.pop() {
            for spread in spreads {
                if let Some(spreads) =
                    self.find_undef_vars_inner(&Scope::Fragment(spread), defined, unused, visited)
                {
                    to_visit.push(spreads);
                }
            }
        }
    }
