    fn clean_up_incoming(&mut self, incoming: &Incoming) {
        self.index.remove_initial(incoming.packet.header.dst_cid);
        let incoming_buffer = self.incoming_buffers.remove(incoming.incoming_idx);
        self.all_incoming_buffers_total_bytes -= incoming_buffer.total_bytes;
    }
