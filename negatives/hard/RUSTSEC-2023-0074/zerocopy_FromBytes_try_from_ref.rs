    #[inline]
    #[doc(hidden)] // TODO(#5): Finalize name before remove this attribute.
    fn try_from_ref(bytes: &[u8]) -> Option<&Self>
    where
        Self: KnownLayout,
    {
        let maybe_self = Ptr::from(bytes).try_cast_into_no_leftover::<Self>()?;

        // SAFETY:
        // - Since `bytes` is an immutable reference, we know that no mutable
        //   references exist to this memory region.
        // - Since `[u8]` contains no `UnsafeCell`s, we know there are no
        //   `&UnsafeCell` references to this memory region.
        // - Since we don't permit implementing `TryFromBytes` for types which
        //   contain `UnsafeCell`s, there are no `UnsafeCell`s in `Self`, and so
        //   the requirement that all references contain `UnsafeCell`s at the
        //   same offsets is trivially satisfied.
        // - All bytes of `bytes` are initialized.
        //
        // This call may panic. If that happens, it doesn't cause any soundness
        // issues, as we have not generated any invalid state which we need to
        // fix before returning.
        if unsafe { !Self::is_bit_valid(maybe_self) } {
            return None;
        }

        // SAFETY:
        // - Preconditions for `as_ref`:
        //   - `is_bit_valid` guarantees that `*maybe_self` contains a valid
        //     `Self`. Since `&[u8]` does not permit interior mutation, this
        //     cannot be invalidated after this method returns.
        //   - Since the argument and return types are immutable references,
        //     Rust will prevent the caller from producing any mutable
        //     references to the same memory region.
        //   - Since `Self` is not allowed to contain any `UnsafeCell`s and the
        //     same is true of `[u8]`, interior mutation is not possible. Thus,
        //     no mutation is possible. For the same reason, there is no
        //     mismatch between the two types in terms of which byte ranges are
        //     referenced as `UnsafeCell`s.
        // - Since interior mutation isn't possible within `Self`, there's no
        //   way for the returned reference to be used to modify the byte range,
        //   and thus there's no way for the returned reference to be used to
        //   write an invalid `[u8]` which would be observable via the original
        //   `&[u8]`.
        Some(unsafe { maybe_self.as_ref() })
    }
