pub fn phone_number(i: &str) -> IResult<&str, Number> {
    let (_, i) = extract(i)?;
    let extension = consts::EXTN_PATTERN.captures(i);

    if let Some(c) = extension.as_ref() {
        if c.get(0).is_none() || c.get(2).is_none() {
            return Err(nom::Err::Failure(nom::error::Error::new(i, ErrorKind::Eof)));
        }
    }

    Ok((
        "",
        Number {
            national: extension
                .as_ref()
                .map(|c| &i[..c.get(0).unwrap().start()])
                .unwrap_or(i)
                .into(),

            extension: extension
                .as_ref()
                .map(|c| c.get(2).unwrap().as_str())
                .map(Into::into),

            ..Default::default()
        },
    ))
}
