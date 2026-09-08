    fn calculate_cksum(&self) -> u32 {
        let old = self.as_old();
        let start = old as *const _ as usize;
        let cksum_start = old.cksum.as_ptr() as *const _ as usize;
        let offset = cksum_start - start;
        let len = old.cksum.len();
        self.bytes[0..offset]
            .iter()
            .chain(iter::repeat(&b' ').take(len))
            .chain(&self.bytes[offset + len..])
            .fold(0, |a, b| a + (*b as u32))
    }
