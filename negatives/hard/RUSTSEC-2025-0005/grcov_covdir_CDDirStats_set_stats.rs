    pub fn set_stats(&mut self, precision: usize) {
        for file in self.files.iter() {
            self.stats.add(&file.stats);
        }
        for dir in self.dirs.iter() {
            let mut dir = dir.borrow_mut();
            dir.set_stats(precision);
            self.stats.add(&dir.stats);
        }
        self.stats.set_percent(precision);
    }
