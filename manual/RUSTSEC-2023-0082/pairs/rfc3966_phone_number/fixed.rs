pub fn phone_number(i: &str) -> IResult<&str, Number> {
    parse! { i =>
        opt(tag_no_case("Tel:"));
        let prefix = opt(prefix);
        let national = take_while1(number);
        check;
        let params = opt(parameters);
    };

    Ok((
        i,
        Number {
            national: (*national).into(),

            prefix: prefix
                .or_else(|| {
                    params
                        .as_ref()
                        .and_then(|m| m.get("phone-context"))
                        .map(|&s| s.strip_prefix('+').unwrap_or(s))
                })
                .map(|cs| cs.into()),

            extension: params
                .as_ref()
                .and_then(|m| m.get("ext"))
                .map(|&cs| cs.into()),

            ..Default::default()
        },
    ))
}
