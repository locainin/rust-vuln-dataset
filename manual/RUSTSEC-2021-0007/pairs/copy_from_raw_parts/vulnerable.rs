    pub fn copy_from_raw_parts<I, IU>(&mut self, mut src: I, mut src_linesize: IU)
    where
        I: Iterator<Item = *const u8>,
        IU: Iterator<Item = usize>,
    {
        if let MediaKind::Video(ref fmt) = self.kind {
            let mut f_iter = fmt.format.iter();
            let width = fmt.width;
            let height = fmt.height;
            for i in 0..self.buf.count() {
                let d_linesize = self.buf.linesize(i).unwrap();
                let s_linesize = src_linesize.next().unwrap();
                let data = self.buf.as_mut_slice(i).unwrap();
                let cc = f_iter.next().unwrap();
                let rr = src.next().unwrap();
                let hb = cc.unwrap().get_height(height);
                let ss = unsafe { slice::from_raw_parts(rr, hb * s_linesize) };
                copy_plane(
                    data,
                    d_linesize,
                    ss,
                    s_linesize,
                    cc.unwrap().get_width(width),
                    hb,
                );
            }
        } else {
            unimplemented!();
        }
    }
