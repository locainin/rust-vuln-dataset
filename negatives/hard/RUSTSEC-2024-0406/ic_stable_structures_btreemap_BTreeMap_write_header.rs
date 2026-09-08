    fn write_header(header: &BTreeHeader, memory: &M) {
        // Serialize the header
        let mut buf = [0; PACKED_HEADER_SIZE];
        buf[0..3].copy_from_slice(MAGIC.as_slice());
        match header.version {
            Version::V1(DerivedPageSize {
                max_key_size,
                max_value_size,
            })
            | Version::V2(PageSize::Derived(DerivedPageSize {
                max_key_size,
                max_value_size,
            })) => {
                buf[3] = LAYOUT_VERSION;
                buf[4..8].copy_from_slice(&max_key_size.to_le_bytes());
                buf[8..12].copy_from_slice(&max_value_size.to_le_bytes());
            }
            Version::V2(PageSize::Value(page_size)) => {
                buf[3] = LAYOUT_VERSION_2;
                buf[4..8].copy_from_slice(&page_size.to_le_bytes());
                buf[8..12].copy_from_slice(&PAGE_SIZE_VALUE_MARKER.to_le_bytes());
            }
        };
        buf[12..20].copy_from_slice(&header.root_addr.get().to_le_bytes());
        buf[20..28].copy_from_slice(&header.length.to_le_bytes());
        // Write the header
        crate::write(memory, 0, &buf);
    }
