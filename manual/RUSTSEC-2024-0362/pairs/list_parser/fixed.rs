#[inline]
fn list_parser<'i, O1, O2>(
    open: char,
    delim: char,
    close: char,
    f: impl Parser<Input<'i>, O1, ContextError>,
) -> impl Parser<Input<'i>, O2, ContextError>
where
    O2: Accumulate<O1>,
{
    #[cfg(feature = "debug")]
    let name = format!("list({open:?}, {delim:?}, {close:?})");
    #[cfg(not(feature = "debug"))]
    let name = "list";

    // These have to be outside of the closure for some reason.
    let f = check_recursion(f);
    let elems_1 = separated(1.., f, (char_parser(delim), space0));
    let mut elems_and_end = terminated(elems_1, (opt(delim), space0, cut_err(char_parser(close))));
    trace(name, move |input: &mut Input<'i>| {
        let _ = char_parser(open).parse_next(input)?;
        let _ = space0(input)?;
        if input.starts_with(close) {
            input.next_slice(close.len());
            return Ok(O2::initial(Some(0)));
        }
        elems_and_end.parse_next(input)
    })
}
