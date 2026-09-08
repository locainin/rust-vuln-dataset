    fn as_z_stream_mut(&mut self) -> &mut z_stream {
        // safety: a valid &mut InflateStream is also a valid &mut z_stream
        unsafe { &mut *(self as *mut _ as *mut z_stream) }
    }
