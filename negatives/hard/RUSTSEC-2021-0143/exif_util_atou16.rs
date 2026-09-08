pub fn atou16(bytes: &[u8]) -> Result<u16, Error> {
    if cfg!(debug_assertions) && bytes.len() >= 5 {
        panic!("atou16 accepts up to 4 bytes");
    }
    if bytes.len() == 0 {
        return Err(Error::InvalidFormat("Not a number"));
    }
    let mut n = 0;
    for &c in bytes {
        if c < ASCII_0 || ASCII_9 < c {
            return Err(Error::InvalidFormat("Not a number"));
        }
        n = n * 10 + (c - ASCII_0) as u16;
    }
    Ok(n)
}
