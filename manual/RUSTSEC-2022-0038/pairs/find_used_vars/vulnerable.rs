    fn find_used_vars(
        &self,
        from: &Scope<'a>,
        defined: &HashSet<&'a str>,
        used: &mut HashSet<&'a str>,
        visited: &mut HashSet<Scope<'a>>,
    ) {
        if visited.contains(from) {
            return;
        }

        visited.insert(from.clone());

        if let Some(used_vars) = self.used_variables.get(from) {
            for var in used_vars {
                if defined.contains(var) {
                    used.insert(var);
                }
            }
        }

        if let Some(spreads) = self.spreads.get(from) {
            for spread in spreads {
                self.find_used_vars(&Scope::Fragment(spread), defined, used, visited);
            }
        }
    }
