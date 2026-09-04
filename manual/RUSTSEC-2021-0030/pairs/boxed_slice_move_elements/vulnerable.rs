    fn move_elements<F>(self, mut f: F)
    where
        F: FnMut(<T as SliceLike>::Element),
    {
        unsafe {
            for item in self.as_element_slice() {
                f(ptr::read(item));
            }

            Box::from_raw((*Box::into_raw(self)).as_element_slice_mut()
                as *mut [<T as SliceLike>::Element]
                as *mut [ManuallyDrop<<T as SliceLike>::Element>]);
        }
    }
