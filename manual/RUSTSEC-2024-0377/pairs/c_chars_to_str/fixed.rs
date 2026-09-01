pub fn c_chars_to_str<const N: usize>(chars: &[c_char; N]) -> Result<&str> {
    // Safety: Casting from i8 to u8 slice should be safe
    let bytes = unsafe { as_u8_slice(chars) };
    let cstr = CStr::from_bytes_until_nul(bytes).map_err(|_| Error::Conversion {
        input: format!("{chars:?}"),
        desired_type: "CStr (null-terminated)",
    })?;

    cstr.to_str()
        .map_err(|e| Error::utf8(e, format!("converting c_char array: {chars:?}")))
}
