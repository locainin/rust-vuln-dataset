    fn enter_directive(
        &mut self,
        ctx: &mut ValidatorContext<'a, S>,
        directive: &'a Spanning<Directive<S>>,
    ) {
        let directive_name = &directive.item.name.item;

        if let Some(directive_type) = ctx.schema.directive_by_name(directive_name) {
            if let Some(current_location) = self.location_stack.last() {
                if !directive_type
                    .locations
                    .iter()
                    .any(|l| l == current_location)
                {
                    ctx.report_error(
                        &misplaced_error_message(directive_name, current_location),
                        &[directive.start],
                    );
                }
            }
        } else {
            ctx.report_error(&unknown_error_message(directive_name), &[directive.start]);
        }
    }
