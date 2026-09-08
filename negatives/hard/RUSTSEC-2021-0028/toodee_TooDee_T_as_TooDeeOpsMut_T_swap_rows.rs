    fn swap_rows(&mut self, mut r1: usize, mut r2: usize) {
        match r1.cmp(&r2) {
            Ordering::Less => {},
            Ordering::Greater => {
                // force r1 < r2
                core::mem::swap(&mut r1, &mut r2);
            },
            Ordering::Equal => {
                // swapping a row with itself
                return;
            }
        }
        assert!(r2 < self.num_rows);
        let num_cols = self.num_cols;
        unsafe {
            let (first, rest) = self.data.get_unchecked_mut(r1 * num_cols..).split_at_mut(num_cols);
            let snd_idx = (r2 - r1 - 1) * num_cols;
            let second = rest.get_unchecked_mut(snd_idx..snd_idx + num_cols);
            // Both slices are guaranteed to have the same length
            debug_assert_eq!(first.len(), num_cols);
            debug_assert_eq!(second.len(), num_cols);
            // We know that the two slices will not overlap because r1 != r2, and we used split_at_mut()
            ptr::swap_nonoverlapping(first.as_mut_ptr(), second.as_mut_ptr(), num_cols);
        }
    }
