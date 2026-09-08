    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        for _ in 0..self.zeros() {
            write!(f, "0")?;
        }

        write!(f, "{}", self.value())
    }
