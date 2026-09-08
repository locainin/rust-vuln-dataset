    pub fn as_raw(&self) -> Result<Vec<u8>, ASN1EncodeErr> {
        match (self.0.get(0), self.0.get(1)) {
            (Some(v1), Some(v2)) => {
                let two = BigUint::from_u8(2).unwrap();

                // first, validate that the first two items meet spec
                if v1 > &two {
                    return Err(ASN1EncodeErr::ObjectIdentVal1TooLarge);
                }

                let u175 = BigUint::from_u8(175).unwrap();
                let u39 = BigUint::from_u8(39).unwrap();
                let bound = if v1 == &two { u175 } else { u39 };

                if v2 > &bound {
                    return Err(ASN1EncodeErr::ObjectIdentVal2TooLarge);
                }

                // the following unwraps must be safe, based on the
                // validation above.
                let value1 = v1.to_u8().unwrap();
                let value2 = v2.to_u8().unwrap();
                let byte1 = (value1 * 40) + value2;

                // now we can build all the rest of the body
                let mut body = vec![byte1];
                for num in self.0.iter().skip(2) {
                    let mut local = encode_base127(&num);
                    body.append(&mut local);
                }

                Ok(body)
            }
            _ => Err(ASN1EncodeErr::ObjectIdentHasTooFewFields),
        }
    }
