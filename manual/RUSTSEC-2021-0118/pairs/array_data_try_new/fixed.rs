    pub fn try_new(
        data_type: DataType,
        len: usize,
        null_count: Option<usize>,
        null_bit_buffer: Option<Buffer>,
        offset: usize,
        buffers: Vec<Buffer>,
        child_data: Vec<ArrayData>,
    ) -> Result<Self> {
        // Safety justification: `validate_full` is called below
        let new_self = unsafe {
            Self::new_unchecked(
                data_type,
                len,
                null_count,
                null_bit_buffer,
                offset,
                buffers,
                child_data,
            )
        };

        // As the data is not trusted, do a full validation of its contents
        new_self.validate_full()?;
        Ok(new_self)
    }
