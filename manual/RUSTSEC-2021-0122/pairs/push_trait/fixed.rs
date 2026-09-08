pub trait Push: Sized {
    type Output;

    /// # Safety
    ///
    /// dst is aligned to [`Self::alignment`] and has length greater than or equal to [`Self::size`]
    unsafe fn push(&self, dst: &mut [u8], written_len: usize);
    #[inline]
    fn size() -> usize {
        size_of::<Self::Output>()
    }
    #[inline]
    fn alignment() -> PushAlignment {
        PushAlignment::new(align_of::<Self::Output>())
    }
}
