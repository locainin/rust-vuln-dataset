    pub unsafe fn new(heap_bottom: *mut u8, heap_size: usize) -> Heap {
        Heap {
            used: 0,
            holes: HoleList::new(heap_bottom, heap_size),
        }
    }
