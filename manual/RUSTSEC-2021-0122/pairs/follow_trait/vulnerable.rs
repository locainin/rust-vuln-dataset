pub trait Follow<'buf> {
    type Inner;
    fn follow(buf: &'buf [u8], loc: usize) -> Self::Inner;
}
