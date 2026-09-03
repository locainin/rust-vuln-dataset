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
        let fragment = match self.named_fragments.get(fragment_name) {
            Some(f) => f,
            None => return,
        };

        let (field_map2, fragment_names2) =
            self.get_referenced_fields_and_fragment_names(fragment, ctx);

        self.collect_conflicts_between(conflicts, mutually_exclusive, field_map, &field_map2, ctx);

        for fragment_name2 in fragment_names2 {
            // Early return on fragment recursion, as it makes no sense.
            // Fragment recursions are prevented by `no_fragment_cycles` validator.
            if fragment_name == fragment_name2 {
                return;
            }
            self.collect_conflicts_between_fields_and_fragment(
                conflicts,
                field_map,
                fragment_name2,
                mutually_exclusive,
                ctx,
            );
        }
    }
