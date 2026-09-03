    fn find_undef_vars(
        &'a self,
        scope: &Scope<'a>,
        defined: &HashSet<&'a str>,
        unused: &mut Vec<&'a Spanning<&'a str>>,
        visited: &mut HashSet<Scope<'a>>,
    ) {
        if visited.contains(scope) {
            return;
        }

        visited.insert(scope.clone());

        if let Some(used_vars) = self.used_variables.get(scope) {
            for var in used_vars {
                if !defined.contains(&var.item) {
                    unused.push(var);
                }
            }
        }

        if let Some(spreads) = self.spreads.get(scope) {
            for spread in spreads {
                self.find_undef_vars(&Scope::Fragment(spread), defined, unused, visited);
            }
        }
    }
