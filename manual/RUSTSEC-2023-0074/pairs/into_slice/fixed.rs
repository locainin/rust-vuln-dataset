    #[inline(always)]
    pub fn into_slice(self) -> &'a [T] {
        assert!(B::INTO_REF_INTO_MUT_ARE_SOUND);

        // SAFETY: According to the safety preconditions on
        // `ByteSlice::INTO_REF_INTO_MUT_ARE_SOUND`, the preceding assert
        // ensures that, given `B: 'a`, it is sound to drop `self` and still
        // access the underlying memory using reads for `'a`.
        unsafe { self.deref_slice_helper() }
    }
