    fn pow_le(&self, bits: &[Boolean<ConstraintF>]) -> Result<Self, SynthesisError> {
        let mut res = Self::one();
        let mut power = self.clone();
        for bit in bits {
            let tmp = res.clone() * &power;
            res = bit.select(&tmp, &res)?;
            power.square_in_place()?;
        }
        Ok(res)
    }
