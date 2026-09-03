    pub unsafe fn new(hole_addr: *mut u8, hole_size: usize) -> HoleList {
        assert_eq!(size_of::<Hole>(), Self::min_size());

        let aligned_hole_addr = align_up(hole_addr, align_of::<Hole>());
        let ptr = aligned_hole_addr as *mut Hole;
        ptr.write(Hole {
            size: hole_size - ((aligned_hole_addr as usize) - (hole_addr as usize)),
            next: None,
        });

        HoleList {
            first: Hole {
                size: 0,
                next: Some(NonNull::new_unchecked(ptr)),
            },
            bottom: aligned_hole_addr,
            top: hole_addr.wrapping_add(hole_size),
        }
    }
