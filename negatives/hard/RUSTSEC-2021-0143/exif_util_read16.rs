pub fn read16<R>(reader: &mut R) -> Result<u16, io::Error> where R: io::Read {
    let mut buf = [0u8; 2];
    reader.read_exact(&mut buf)?;
    Ok(u16::from_be_bytes(buf))
}
