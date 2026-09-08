    fn fmt(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
        let do_display = |formatter: &mut fmt::Formatter| -> fmt::Result {
            write!(formatter, "{}.{}.{}", self.major, self.minor, self.patch)?;
            if !self.pre.is_empty() {
                write!(formatter, "-{}", self.pre)?;
            }
            if !self.build.is_empty() {
                write!(formatter, "+{}", self.build)?;
            }
            Ok(())
        };

        let do_len = || -> usize {
            digits(self.major)
                + 1
                + digits(self.minor)
                + 1
                + digits(self.patch)
                + !self.pre.is_empty() as usize
                + self.pre.len()
                + !self.build.is_empty() as usize
                + self.build.len()
        };

        pad(formatter, do_display, do_len)
    }
