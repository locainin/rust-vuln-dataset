    fn collect_incorrect_usages(
        &self,
        from: &Scope<'a>,
        var_defs: &[&'a (Spanning<&'a str>, VariableDefinition<S>)],
        ctx: &mut ValidatorContext<'a, S>,
        visited: &mut HashSet<Scope<'a>>,
    ) {
        if visited.contains(from) {
            return;
        }

        visited.insert(from.clone());

        if let Some(usages) = self.variable_usages.get(from) {
            for &(ref var_name, ref var_type) in usages {
                if let Some(&&(ref var_def_name, ref var_def)) = var_defs
                    .iter()
                    .find(|&&&(ref n, _)| n.item == var_name.item)
                {
                    let expected_type = match (&var_def.default_value, &var_def.var_type.item) {
                        (&Some(_), &Type::List(ref inner, expected_size)) => {
                            Type::NonNullList(inner.clone(), expected_size)
                        }
                        (&Some(_), &Type::Named(ref inner)) => {
                            Type::NonNullNamed(Cow::Borrowed(inner))
                        }
                        (_, t) => t.clone(),
                    };

                    if !ctx.schema.is_subtype(&expected_type, var_type) {
                        ctx.report_error(
                            &error_message(var_name.item, expected_type, var_type),
                            &[var_def_name.start, var_name.start],
                        );
                    }
                }
            }
        }

        if let Some(spreads) = self.spreads.get(from) {
            for spread in spreads {
                self.collect_incorrect_usages(&Scope::Fragment(spread), var_defs, ctx, visited);
            }
        }
    }
