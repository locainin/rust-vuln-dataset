#[cfg_attr(feature = "no-panic", no_panic)]
fn enc_16lsd<const OFFSET: usize>(buf: &mut [MaybeUninit<u8>], n: u64) {
    // Consume the least-significant decimals from a working copy.
    let mut remain = n;

    // Format per four digits from the lookup table.
    for quad_index in (1..4).rev() {
        // pull two pairs
        let quad = remain % 1_00_00;
        remain /= 1_00_00;
        let (pair1, pair2) = divmod100(quad as u32);
        unsafe {
            buf[quad_index * 4 + OFFSET + 0]
                .write(*DECIMAL_PAIRS.0.get_unchecked(pair1 as usize * 2 + 0));
            buf[quad_index * 4 + OFFSET + 1]
                .write(*DECIMAL_PAIRS.0.get_unchecked(pair1 as usize * 2 + 1));
            buf[quad_index * 4 + OFFSET + 2]
                .write(*DECIMAL_PAIRS.0.get_unchecked(pair2 as usize * 2 + 0));
            buf[quad_index * 4 + OFFSET + 3]
                .write(*DECIMAL_PAIRS.0.get_unchecked(pair2 as usize * 2 + 1));
        }
    }

    // final two pairs
    let (pair1, pair2) = divmod100(remain as u32);
    unsafe {
        buf[OFFSET + 0].write(*DECIMAL_PAIRS.0.get_unchecked(pair1 as usize * 2 + 0));
        buf[OFFSET + 1].write(*DECIMAL_PAIRS.0.get_unchecked(pair1 as usize * 2 + 1));
        buf[OFFSET + 2].write(*DECIMAL_PAIRS.0.get_unchecked(pair2 as usize * 2 + 0));
        buf[OFFSET + 3].write(*DECIMAL_PAIRS.0.get_unchecked(pair2 as usize * 2 + 1));
    }
}
