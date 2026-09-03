    fn collect_conflicts_between_fields_and_fragment(
        &self,
        conflicts: &mut Vec<Conflict>,
        field_map: &AstAndDefCollection<'a, S>,
        fragment_name: &str,
        mutually_exclusive: bool,
        ctx: &ValidatorContext<'a, S>,
    ) where
        S: ScalarValue,
    {
        let mut to_check = Vec::new();
        if let Some(fragments) = self.collect_conflicts_between_fields_and_fragment_inner(
            conflicts,
            field_map,
            fragment_name,
            mutually_exclusive,
            ctx,
        ) {
            to_check.push((fragment_name, fragments))
        }

        while let Some((fragment_name, fragment_names2)) = to_check.pop() {
            for fragment_name2 in fragment_names2 {
                // Early return on fragment recursion, as it makes no sense.
                // Fragment recursions are prevented by `no_fragment_cycles` validator.
                if fragment_name == fragment_name2 {
                    return;
                }
                if let Some(fragments) = self.collect_conflicts_between_fields_and_fragment_inner(
                    conflicts,
                    field_map,
                    fragment_name2,
                    mutually_exclusive,
                    ctx,
                ) {
                    to_check.push((fragment_name2, fragments));
                };
            }
        }
    }
