            fn read_bytes_default_le(bytes: &[u8]) -> Self {
                let mut pos = 0;
                let len = T::BYTE_LEN;
                let mut result: Self;
                unsafe {
                    result = std::mem::uninitialized();
                    for i in 0 .. ($x) {
                        std::ptr::write(&mut result[i], <T>::read_bytes_default_le(&bytes[pos .. pos + len]));
                        pos += len;
                    }
                }
                result
            }
