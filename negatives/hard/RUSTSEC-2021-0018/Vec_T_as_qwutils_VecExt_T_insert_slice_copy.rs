    #[inline]
    fn insert_slice_copy(&mut self, index: usize, slice: &[T]) where T: Copy {
        let vlen = self.len();
        let slen = slice.len();
        assert!(index <= vlen);
        assert!(slice.len() <= isize::MAX as usize); //no UB plz
        let dlen = vlen+slen;

        if dlen > self.capacity() {
            self.reserve(slice.len());
        }

        unsafe {
            {
                let s = slice.as_ptr();
                let p = self.as_mut_ptr().add(index);
                ptr::copy(p, p.add(slen), vlen - index);
                ptr::copy_nonoverlapping(s, p, slen);
            }
            self.set_len(dlen);
        }
    }
