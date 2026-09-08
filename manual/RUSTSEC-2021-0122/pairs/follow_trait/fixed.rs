pub trait Follow<'buf> {
    type Inner;
    /// # Safety
    ///
    /// `buf[loc..]` must contain a valid value of `Self` and anything it
    /// transitively refers to by offset must also be valid
    unsafe fn follow(buf: &'buf [u8], loc: usize) -> Self::Inner;
}
