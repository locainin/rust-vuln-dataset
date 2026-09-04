    #[inline]
    fn insert_slice_clone(&mut self, index: usize, slice: &[T]) where T: Clone {
        let vlen = self.len();
        let slen = slice.len();
        assert!(index <= vlen);
        assert!(slice.len() <= isize::MAX as usize); //no UB plz
        let dlen = vlen+slen;

        if dlen > self.capacity() {
            self.reserve(slice.len());
        }

        unsafe {
            self.set_len(0);
            {
                let mut p = self.as_mut_ptr().add(index);
                ptr::copy(p, p.add(slen), vlen - index);
                for v in slice {
                    ptr::write(p,v.clone());
                    p = p.offset(1);
                }
            }
            self.set_len(dlen);
        }
    }
