    fn enter_field(
        &mut self,
        context: &mut ValidatorContext<'a, S>,
        field: &'a Spanning<Field<S>>,
    ) {
        {
            if let Some(parent_type) = context.parent_type() {
                let field_name = &field.item.name;
                let type_name = parent_type.name().unwrap_or("<unknown>");

                if parent_type.field_by_name(field_name.item).is_none() {
                    if let MetaType::Union(..) = *parent_type {
                        // You can query for `__typename` on a union,
                        // but it isn't a field on the union...it is
                        // instead on the resulting object returned.
                        if field_name.item == "__typename" {
                            return;
                        }
                    }

                    context.report_error(
                        &error_message(field_name.item, type_name),
                        &[field_name.start],
                    );
                }
            }
        }
    }
