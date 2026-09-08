    pub fn from_vec(buffer: Vec<u8>) -> Self {
        // we need to check the size here because we create the backing buffer
        // directly, bypassing the typical way of using grow_owned_buf:
        assert!(
            buffer.len() <= FLATBUFFERS_MAX_BUFFER_SIZE,
            "cannot initialize buffer bigger than 2 gigabytes"
        );
        let head = buffer.len();
        FlatBufferBuilder {
            owned_buf: buffer,
            head,

            field_locs: Vec::new(),
            written_vtable_revpos: Vec::new(),

            nested: false,
            finished: false,

            min_align: 0,
            force_defaults: false,
            strings_pool: Vec::new(),

            _phantom: PhantomData,
        }
    }
