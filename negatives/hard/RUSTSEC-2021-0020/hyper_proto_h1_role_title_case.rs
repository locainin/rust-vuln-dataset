fn title_case(dst: &mut Vec<u8>, name: &[u8]) {
    dst.reserve(name.len());

    let mut iter = name.iter();

    // Uppercase the first character
    if let Some(c) = iter.next() {
        if *c >= b'a' && *c <= b'z' {
            dst.push(*c ^ b' ');
        } else {
            dst.push(*c);
        }
    }

    while let Some(c) = iter.next() {
        dst.push(*c);

        if *c == b'-' {
            if let Some(c) = iter.next() {
                if *c >= b'a' && *c <= b'z' {
                    dst.push(*c ^ b' ');
                } else {
                    dst.push(*c);
                }
            }
        }
    }
}
