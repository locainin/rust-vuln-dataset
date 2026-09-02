    fn update_max_dynamic_size(&mut self, buf: &[u8]) -> usize {
        let (new_size, consumed) = decode_integer(buf, 5).ok().unwrap();
        self.header_table.dynamic_table.set_max_table_size(new_size);

        info!("Decoder changed max table size from {} to {}",
              self.header_table.dynamic_table.get_size(),
              new_size);

        consumed
    }
