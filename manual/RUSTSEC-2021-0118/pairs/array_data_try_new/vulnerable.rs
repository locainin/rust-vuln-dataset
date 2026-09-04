    pub fn try_new(
        data_type: DataType,
        len: usize,
        null_count: Option<usize>,
        null_bit_buffer: Option<Buffer>,
        offset: usize,
        buffers: Vec<Buffer>,
        child_data: Vec<ArrayData>,
    ) -> Result<Self> {
        // Safetly justification: `validate` is (will be) called below
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

        new_self.validate()?;
        Ok(new_self)
    }
