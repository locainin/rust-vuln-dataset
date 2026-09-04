    fn mul_by_inverse(&self, d: &Self) -> Result<Self, SynthesisError> {
        let d_inv = if self.is_constant() || d.is_constant() {
            d.inverse()?
        } else {
            Self::new_witness(self.cs(), || Ok(d.value()?.inverse().unwrap_or(F::zero())))?
        };
        Ok(d_inv * self)
    }
