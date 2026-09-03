    fn find_used_vars(
        &'a self,
        from: &Scope<'a>,
        defined: &HashSet<&'a str>,
        used: &mut HashSet<&'a str>,
        visited: &mut HashSet<Scope<'a>>,
    ) {
        let mut to_visit = Vec::new();
        if let Some(spreads) = self.find_used_vars_inner(from, defined, used, visited) {
            to_visit.push(spreads);
        }
        while let Some(spreads) = to_visit.pop() {
            for spread in spreads {
                if let Some(spreads) =
                    self.find_used_vars_inner(&Scope::Fragment(spread), defined, used, visited)
                {
                    to_visit.push(spreads);
                }
            }
        }
    }
