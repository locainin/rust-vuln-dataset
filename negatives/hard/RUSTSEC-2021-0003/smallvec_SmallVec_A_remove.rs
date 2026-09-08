    pub fn remove(&mut self, index: usize) -> A::Item {
        unsafe {
            let (mut ptr, len_ptr, _) = self.triple_mut();
            let len = *len_ptr;
            assert!(index < len);
            *len_ptr = len - 1;
            ptr = ptr.add(index);
            let item = ptr::read(ptr);
            ptr::copy(ptr.add(1), ptr, len - index - 1);
            item
        }
    }
