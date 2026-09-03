    pub unsafe fn extend(&mut self, by: usize) {
        let top = self.top();
        let layout = Layout::from_size_align(by, 1).unwrap();
        self.holes
            .deallocate(NonNull::new_unchecked(top as *mut u8), layout);
        self.holes.top = self.holes.top.add(by);
    }
