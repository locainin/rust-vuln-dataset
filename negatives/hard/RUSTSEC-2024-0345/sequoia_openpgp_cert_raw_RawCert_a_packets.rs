    pub fn packets(&self) -> impl Iterator<Item=RawPacket> {
        let data: &[u8] = self.data.as_ref();

        let count = self.packets.len();
        (0..count)
            .map(move |i| {
                let (tag, header_len, start) = self.packets[i];
                let following = self.packets
                    .get(i + 1)
                    .map(|&(_, _, offset)| offset)
                    .unwrap_or(data.len());

                RawPacket::new(tag, header_len, &data[start..following])
            })
    }
