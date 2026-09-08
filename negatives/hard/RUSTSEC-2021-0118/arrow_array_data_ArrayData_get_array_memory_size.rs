    pub fn get_array_memory_size(&self) -> usize {
        let mut size = mem::size_of_val(self);

        // Calculate rest of the fields top down which contain actual data
        for buffer in &self.buffers {
            size += mem::size_of::<Buffer>();
            size += buffer.capacity();
        }
        if let Some(bitmap) = &self.null_bitmap {
            // this includes the size of the bitmap struct itself, since it is stored directly in
            // this struct we already counted those bytes in the size_of_val(self) above
            size += bitmap.get_array_memory_size();
            size -= mem::size_of::<Bitmap>();
        }
        for child in &self.child_data {
            size += child.get_array_memory_size();
        }

        size
    }
