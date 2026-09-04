    fn mul_by_inverse(&self, d: &Self) -> Result<Self, SynthesisError> {
        let d_inv = d.inverse()?;
        Ok(d_inv * self)
    }
