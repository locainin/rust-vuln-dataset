    fn escape_href(&mut self, buffer: &[u8]) -> io::Result<()> {
        lazy_static! {
            static ref HREF_SAFE: [bool; 256] = {
                let mut a = [false; 256];
                for &c in b"-_.+!*'(),%#@?=;:/,+&$~abcdefghijklmnopqrstuvwxyz".iter() {
                    a[c as usize] = true;
                }
                for &c in b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789".iter() {
                    a[c as usize] = true;
                }
                a
            };
        }

        let size = buffer.len();
        let mut i = 0;

        while i < size {
            let org = i;
            while i < size && HREF_SAFE[buffer[i] as usize] {
                i += 1;
            }

            if i > org {
                self.output.write_all(&buffer[org..i])?;
            }

            if i >= size {
                break;
            }

            match buffer[i] as char {
                '&' => {
                    self.output.write_all(b"&amp;")?;
                }
                '\'' => {
                    self.output.write_all(b"&#x27;")?;
                }
                _ => write!(self.output, "%{:02X}", buffer[i])?,
            }

            i += 1;
        }

