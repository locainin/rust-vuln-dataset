    #[inline(always)]
    pub fn into_mut_slice(mut self) -> &'a mut [T] {
        assert!(B::INTO_REF_INTO_MUT_ARE_SOUND);

        // SAFETY: According to the safety preconditions on
        // `ByteSlice::INTO_REF_INTO_MUT_ARE_SOUND`, the preceding assert
        // ensures that, given `B: 'a + ByteSliceMut`, it is sound to drop
        // `self` and still access the underlying memory using both reads and
        // writes for `'a`.
        unsafe { self.deref_mut_slice_helper() }
    }
