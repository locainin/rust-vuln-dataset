    pub fn new(value: u64, zeros: u8) -> Result<Self, crate::error::Parse> {
        // E.164 specifies a maximum of 15 decimals, which corresponds to slightly over 48.9 bits.
        // 56 bits ought to cut it here.
        if value >= (1 << 56) {
            return Err(crate::error::Parse::TooLong);
        }

        Ok(Self {
            value: ((zeros as u64) << 56) | value,
        })
    }
