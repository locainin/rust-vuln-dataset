    pub fn insert_row<I>(&mut self, index: usize, data: impl IntoIterator<Item=T, IntoIter=I>)
    where I : Iterator<Item=T> + ExactSizeIterator
    {
        assert!(index <= self.num_rows);
        let iter = data.into_iter();
        if self.num_rows == 0 {
            self.num_cols = iter.len();
        } else {
            assert_eq!(self.num_cols, iter.len());
        }
        
        self.reserve(self.num_cols);

        let start = index * self.num_cols;
        let len = self.data.len();

        unsafe {

            // Prevent duplicate (or any) drops on the portion of the array we are modifying.
            // This is to safe-guard against a panic potentially caused by `iter.next()`.
            // Alternative (less performant) approaches would be:
            // - append the new row to the array and use `slice.rotate...()` to shuffle everything into place.
            // - store the new row data in a temporary location before shifting the memory and inserting the row.
            self.data.set_len(start);
            
            let mut p = self.data.as_mut_ptr().add(start);
            // shift everything to make space for the new row
            ptr::copy(p, p.add(self.num_cols), len - start);

            let mut elem_count = 0usize;
            // Use `take()` to cap the number of elements processed because we cannot rely on
            // then `len()` value of `ExactSizeIterator` in unsafe code.
            for e in iter.take(self.num_cols) {
                ptr::write(p, e);
                p = p.add(1);
                elem_count += 1;
            }
            
            // abort if the iterator length was less than expected
            assert_eq!(self.num_cols, elem_count, "unexpected iterator length");
            
            self.data.set_len(len + self.num_cols);
        }

        // update the number of rows
        self.num_rows += 1;

    }
