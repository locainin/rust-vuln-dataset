    pub fn new(
        width: usize,
        height: usize,
        flipped: bool,
        frame_type: FrameType,
        format: Arc<Formaton>,
    ) -> Self {
        let bits = format.get_total_depth();
        VideoInfo {
            width,
            height,
            flipped,
            frame_type,
            format,
            bits,
        }
    }
