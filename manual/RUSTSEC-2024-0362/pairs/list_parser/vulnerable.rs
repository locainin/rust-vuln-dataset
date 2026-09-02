#[inline]
fn list_parser<'i, O1, O2, E>(
    open: char,
    delim: char,
    close: char,
    f: impl Parser<&'i str, O1, E>,
) -> impl Parser<&'i str, O2, E>
where
    O2: Accumulate<O1>,
    E: ParserError<&'i str> + AddContext<&'i str, StrContext>,
{
    #[cfg(feature = "debug")]
    let name = format!("list({open:?}, {delim:?}, {close:?})");
    #[cfg(not(feature = "debug"))]
    let name = "list";

    // These have to be outside of the closure for some reason.
    let elems_1 = separated(1.., f, (char_parser(delim), space0));
    let mut elems_and_end = terminated(elems_1, (opt(delim), space0, cut_err(char_parser(close))));
    trace(name, move |input: &mut &'i str| {
        let _ = char_parser(open).parse_next(input)?;
        let _ = space0(input)?;
        if let Some(stripped) = input.strip_prefix(close) {
            *input = stripped;
            return Ok(O2::initial(Some(0)));
        }
        elems_and_end.parse_next(input)
    })
}
