    fn encode(&mut self, frame: &[u8], buf: &mut Vec<u8>) {
        match frame.len() {
            0 => {
                match self.escape_count {
                    0 => buf.extend_from_slice(b"\r\n.\r\n"),
                    1 => buf.extend_from_slice(b"\n.\r\n"),
                    2 => buf.extend_from_slice(b".\r\n"),
                    _ => unreachable!(),
                }
                self.escape_count = 0;
            }
            _ => {
                let mut start = 0;
                for (idx, byte) in frame.iter().enumerate() {
                    match self.escape_count {
                        0 => self.escape_count = if *byte == b'\r' { 1 } else { 0 },
                        1 => self.escape_count = if *byte == b'\n' { 2 } else { 0 },
                        2 => self.escape_count = if *byte == b'.' { 3 } else { 0 },
                        _ => unreachable!(),
                    }
                    if self.escape_count == 3 {
                        self.escape_count = 0;
                        buf.extend_from_slice(&frame[start..idx]);
                        buf.extend_from_slice(b".");
                        start = idx;
                    }
                }
                buf.extend_from_slice(&frame[start..]);
            }
        }
    }
