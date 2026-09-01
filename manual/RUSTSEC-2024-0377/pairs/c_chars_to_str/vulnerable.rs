pub fn c_chars_to_str<const N: usize>(chars: &[c_char; N]) -> Result<&str> {
    let cstr = unsafe { CStr::from_ptr(chars.as_ptr()) };
    cstr.to_str()
        .map_err(|e| Error::utf8(e, format!("converting c_char array: {chars:?}")))
}
