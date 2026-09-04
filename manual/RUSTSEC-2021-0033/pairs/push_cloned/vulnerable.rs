    pub fn push_cloned(&mut self, v: &[T]) -> Result<(), ()> {
        self.push_inner(&v).map(|d| unsafe {
            let mut ptr = d.as_mut_ptr() as *mut T;
            for val in v {
                ptr::write(ptr, val.clone());
                ptr = ptr.offset(1);
            }
        })
    }
