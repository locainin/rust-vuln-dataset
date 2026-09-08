    #[inline]
    pub fn try_basic_solidity(self) -> Result<()> {
        match self.0 {
            "address" | "bool" | "string" | "bytes" | "uint" | "int" | "function" => Ok(()),
            name => {
                if let Some(sz) = name.strip_prefix("bytes") {
                    if let Ok(sz) = sz.parse::<usize>() {
                        if sz != 0 && sz <= 32 {
                            return Ok(());
                        }
                    }
                    return Err(Error::invalid_size(name));
                }

                // fast path both integer types
                let s = name.strip_prefix('u').unwrap_or(name);

                if let Some(sz) = s.strip_prefix("int") {
                    if let Ok(sz) = sz.parse::<usize>() {
                        if sz != 0 && sz <= 256 && sz % 8 == 0 {
                            return Ok(());
                        }
                    }
                    return Err(Error::invalid_size(name));
                }

                Err(Error::invalid_type_string(name))
            }
        }
    }
