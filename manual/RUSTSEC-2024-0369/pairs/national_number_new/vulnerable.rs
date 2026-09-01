    pub fn new(value: u64, zeros: u8) -> Self {
        // E.164 specifies a maximum of 15 decimals, which corresponds to slightly over 48.9 bits.
        // 56 bits ought to cut it here.
        assert!(value < (1 << 56), "number too long");
        Self {
            value: ((zeros as u64) << 56) | value,
        }
    }
