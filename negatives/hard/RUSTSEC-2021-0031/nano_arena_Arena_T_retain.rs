    pub fn retain<F: FnMut(&T) -> bool>(&mut self, mut f: F) {
        let len = self.values.len();
        let mut del = 0;

        for i in 0..len {
            if !f(&self.values[i].1) {
                del += 1;
            } else {
                self.swap_index(i - del, i);
            }
        }

        if del > 0 {
            self.truncate(len - del);
        }
    }
