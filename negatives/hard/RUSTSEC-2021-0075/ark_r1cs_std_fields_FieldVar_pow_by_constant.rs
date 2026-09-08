    fn pow_by_constant<S: AsRef<[u64]>>(&self, exp: S) -> Result<Self, SynthesisError> {
        let mut res = Self::one();
        for i in BitIteratorBE::without_leading_zeros(exp) {
            res.square_in_place()?;
            if i {
                res *= self;
            }
        }
        Ok(res)
    }
