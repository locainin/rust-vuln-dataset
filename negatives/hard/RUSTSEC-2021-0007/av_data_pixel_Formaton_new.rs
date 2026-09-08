    pub fn new(
        model: ColorModel,
        components: &[Chromaton],
        elem_size: u8,
        be: bool,
        alpha: bool,
        palette: bool,
    ) -> Self {
        let mut c: [Option<Chromaton>; 5] = [None; 5];

        if components.len() > 5 {
            panic!("too many components");
        }

        for (i, v) in components.iter().enumerate() {
            c[i] = Some(*v);
        }

        Formaton {
            model,

            primaries: ColorPrimaries::Unspecified,
            xfer: TransferCharacteristic::Unspecified,
            matrix: MatrixCoefficients::Unspecified,
            chroma_location: ChromaLocation::Unspecified,

            components: components.len() as u8,
            comp_info: c,
            elem_size,
            be,
            alpha,
            palette,
        }
    }
