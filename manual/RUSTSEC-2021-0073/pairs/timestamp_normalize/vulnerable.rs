    #[cfg(feature = "std")]
    pub fn normalize(&mut self) {
        // Make sure nanos is in the range.
        if self.nanos <= -NANOS_PER_SECOND || self.nanos >= NANOS_PER_SECOND {
            self.seconds += (self.nanos / NANOS_PER_SECOND) as i64;
            self.nanos %= NANOS_PER_SECOND;
        }

        // For Timestamp nanos should be in the range [0, 999999999].
        if self.nanos < 0 {
            self.seconds -= 1;
            self.nanos += NANOS_PER_SECOND;
        }

        // TODO: should this be checked?
        // debug_assert!(self.seconds >= -62_135_596_800 && self.seconds <= 253_402_300_799,
        //               "invalid timestamp: {:?}", self);
    }
