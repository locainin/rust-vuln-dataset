fn comparator(input: &str) -> Result<(Comparator, Position, &str), Error> {
    let (mut op, text) = op(input);
    let default_op = input.len() == text.len();
    let text = text.trim_start_matches(' ');

    let mut pos = Position::Major;
    let (major, text) = numeric_identifier(text, pos)?;
    let mut has_wildcard = false;

    let (minor, text) = if let Some(text) = text.strip_prefix('.') {
        pos = Position::Minor;
        if let Some((_, text)) = wildcard(text) {
            has_wildcard = true;
            if default_op {
                op = Op::Wildcard;
            }
            (None, text)
        } else {
            let (minor, text) = numeric_identifier(text, pos)?;
            (Some(minor), text)
        }
    } else {
        (None, text)
    };

    let (patch, text) = if let Some(text) = text.strip_prefix('.') {
        pos = Position::Patch;
        if let Some((_, text)) = wildcard(text) {
            if default_op {
                op = Op::Wildcard;
            }
            (None, text)
        } else if has_wildcard {
            return Err(Error::new(ErrorKind::UnexpectedAfterWildcard));
        } else {
            let (patch, text) = numeric_identifier(text, pos)?;
            (Some(patch), text)
        }
    } else {
        (None, text)
    };

    let (pre, text) = if patch.is_some() && text.starts_with('-') {
        pos = Position::Pre;
        let text = &text[1..];
        let (pre, text) = prerelease_identifier(text)?;
        if pre.is_empty() {
            return Err(Error::new(ErrorKind::EmptySegment(pos)));
        }
        (pre, text)
    } else {
        (Prerelease::EMPTY, text)
    };

    let text = if patch.is_some() && text.starts_with('+') {
        pos = Position::Build;
        let text = &text[1..];
        let (build, text) = build_identifier(text)?;
        if build.is_empty() {
            return Err(Error::new(ErrorKind::EmptySegment(pos)));
        }
        text
    } else {
        text
    };

    let text = text.trim_start_matches(' ');

    let comparator = Comparator {
        op,
        major,
        minor,
        patch,
        pre,
    };

    Ok((comparator, pos, text))
}
