fn lowercase(s: &str, f: &mut fmt::Formatter) -> fmt::Result {
    let mut chars = s.chars().peekable();
    while let Some(c) = chars.next() {
        if c == 'Σ' && chars.peek().is_none() {
            write!(f, "ς")?;
        } else {
            write!(f, "{}", c.to_lowercase())?;
        }
    }

    Ok(())
}
