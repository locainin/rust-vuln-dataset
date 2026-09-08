    pub fn as_vec<'a, T: TryFrom<&'a BigUint>>(&'a self) -> Result<Vec<T>, ASN1DecodeErr> {
        let mut vec = Vec::new();
        for val in self.0.iter() {
            let ul = match T::try_from(val) {
                Ok(a) => a,
                Err(_) => return Err(ASN1DecodeErr::Overflow),
            };
            vec.push(ul);
        }

        Ok(vec)
    }
