            fn read_bytes_default_le(bytes: &[u8]) -> Self {
                let len = T::BYTE_LEN;
                (0 .. ($x)).map(|i| {
                    <T>::read_bytes_default_le(&bytes[i * len .. (i + 1) * len])
                }).collect::<Vec<_>>().try_into().map_err(|_|()).unwrap()
            }
