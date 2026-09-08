pub fn extract(value: &str) -> IResult<&str, &str> {
    let (mut result, start) = if let Some(index) = consts::VALID_START_CHAR.find(value) {
        (&value[index.start()..], index.start())
    } else {
        return Err(nom::Err::Error(make_error(value, ErrorKind::RegexpMatch)));
    };

    if let Some(trailing) = consts::UNWANTED_END_CHARS.find(result) {
        result = &result[..trailing.start()];
    }

    if let Some(extra) = consts::SECOND_NUMBER_START.find(result) {
        result = &result[..extra.start()];
    }

    if result.is_empty() {
        Err(nom::Err::Error(make_error(value, ErrorKind::RegexpMatch)))
    } else {
        Ok((&value[start + result.len()..], result))
    }
}
