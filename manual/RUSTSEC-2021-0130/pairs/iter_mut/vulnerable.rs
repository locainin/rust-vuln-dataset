    pub fn iter_mut<'a>(&'_ mut self) -> IterMut<'a, K, V> {
        IterMut {
            len: self.len(),
            ptr: unsafe { (*self.head).next },
            end: unsafe { (*self.tail).prev },
            phantom: PhantomData,
        }
    }
