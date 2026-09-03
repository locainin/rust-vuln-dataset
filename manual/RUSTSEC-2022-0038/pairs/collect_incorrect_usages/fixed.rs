    fn collect_incorrect_usages<'me>(
        &'me self,
        from: &Scope<'a>,
        var_defs: &[&'a (Spanning<&'a str>, VariableDefinition<S>)],
        ctx: &mut ValidatorContext<'a, S>,
        visited: &mut HashSet<Scope<'a>>,
    ) {
        let mut to_visit = Vec::new();
        if let Some(spreads) = self.collect_incorrect_usages_inner(from, var_defs, ctx, visited) {
            to_visit.push(spreads);
        }

        while let Some(spreads) = to_visit.pop() {
            for spread in spreads {
                if let Some(spreads) = self.collect_incorrect_usages_inner(
                    &Scope::Fragment(spread),
                    var_defs,
                    ctx,
                    visited,
                ) {
                    to_visit.push(spreads);
                }
            }
        }
    }
