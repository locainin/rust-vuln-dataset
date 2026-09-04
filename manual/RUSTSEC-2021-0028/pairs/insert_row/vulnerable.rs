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
            let mut p = self.data.as_mut_ptr().add(start);
            // shift everything to make space for the new row
            ptr::copy(p, p.add(self.num_cols), len - start);
            for e in iter {
                ptr::write(p, e);
                p = p.add(1);
            }
            self.data.set_len(len + self.num_cols);
        }

        // update the number of rows
        self.num_rows += 1;

    }
