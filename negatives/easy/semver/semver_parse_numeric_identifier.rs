fn numeric_identifier(input: &str, pos: Position) -> Result<(u64, &str), Error> {
    let mut len = 0;
    let mut value = 0u64;

    while let Some(&digit) = input.as_bytes().get(len) {
        if digit < b'0' || digit > b'9' {
            break;
        }
        if value == 0 && len > 0 {
            return Err(Error::new(ErrorKind::LeadingZero(pos)));
        }
        match value
            .checked_mul(10)
            .and_then(|value| value.checked_add((digit - b'0') as u64))
        {
            Some(sum) => value = sum,
            None => return Err(Error::new(ErrorKind::Overflow(pos))),
        }
        len += 1;
    }

    if len > 0 {
        Ok((value, &input[len..]))
    } else if let Some(unexpected) = input[len..].chars().next() {
        Err(Error::new(ErrorKind::UnexpectedChar(pos, unexpected)))
    } else {
        Err(Error::new(ErrorKind::UnexpectedEnd(pos)))
    }
}
