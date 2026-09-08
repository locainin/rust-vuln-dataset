pub trait Push: Sized {
    type Output;
    fn push(&self, dst: &mut [u8], _rest: &[u8]);
    #[inline]
    fn size() -> usize {
        size_of::<Self::Output>()
    }
    #[inline]
    fn alignment() -> PushAlignment {
        PushAlignment::new(align_of::<Self::Output>())
    }
}
