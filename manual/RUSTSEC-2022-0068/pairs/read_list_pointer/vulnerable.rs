    #[inline]
    pub unsafe fn read_list_pointer(
        mut arena: &dyn ReaderArena,
        mut segment_id: u32,
        cap_table: CapTableReader,
        mut reff: *const WirePointer,
        default_value: *const u8,
        expected_element_size: Option<ElementSize>,
        nesting_limit: i32,
    ) -> Result<ListReader<'_>> {
        if (*reff).is_null() {
            if default_value.is_null() || (*(default_value as *const WirePointer)).is_null() {
                return Ok(ListReader::new_default());
            }
            reff = default_value as *const _;
            arena = &super::NULL_ARENA;
            segment_id = 0;
        }

        if nesting_limit <= 0 {
            return Err(Error::failed("nesting limit exceeded".to_string()));
        }
        let (mut ptr, reff, segment_id) = follow_fars(arena, reff, segment_id)?;

        if (*reff).kind() != WirePointerKind::List {
            return Err(Error::failed(
                "Message contains non-list pointer where list pointer was expected".to_string(),
            ));
        }

        let element_size = (*reff).list_element_size();
        match element_size {
            InlineComposite => {
                let word_count = (*reff).list_inline_composite_word_count();

                let tag: *const WirePointer = ptr as *const WirePointer;

                ptr = ptr.add(BYTES_PER_WORD);

                bounds_check(
                    arena,
                    segment_id,
                    ptr.offset(-(BYTES_PER_WORD as isize)),
                    word_count as usize + 1,
                    WirePointerKind::List,
                )?;

                if (*tag).kind() != WirePointerKind::Struct {
                    return Err(Error::failed(
                        "InlineComposite lists of non-STRUCT type are not supported.".to_string(),
                    ));
                }

                let size = (*tag).inline_composite_list_element_count();
                let data_size = (*tag).struct_data_size();
                let ptr_count = (*tag).struct_ptr_count();
                let words_per_element = (*tag).struct_word_size();

                if u64::from(size) * u64::from(words_per_element) > u64::from(word_count) {
                    return Err(Error::failed(
                        "InlineComposite list's elements overrun its word count.".to_string(),
                    ));
                }

                if words_per_element == 0 {
                    // Watch out for lists of zero-sized structs, which can claim to be
                    // arbitrarily large without having sent actual data.
                    amplified_read(arena, u64::from(size))?;
                }

                // If a struct list was not expected, then presumably a non-struct list was upgraded
                // to a struct list. We need to manipulate the pointer to point at the first field
                // of the struct. Together with the `step` field, this will allow the struct list to
                // be accessed as if it were a primitive list without branching.

                // Check whether the size is compatible.
                match expected_element_size {
                    None | Some(Void) | Some(InlineComposite) => (),
                    Some(Bit) => {
                        return Err(Error::failed(
                            "Found struct list where bit list was expected.".to_string(),
                        ));
                    }
                    Some(Byte) | Some(TwoBytes) | Some(FourBytes) | Some(EightBytes) => {
                        if data_size == 0 {
                            return Err(Error::failed(
                                "Expected a primitive list, but got a list of pointer-only structs"
                                    .to_string(),
                            ));
                        }
                    }
                    Some(Pointer) => {
                        // We expected a list of pointers but got a list of structs. Assuming the
                        // first field in the struct is the pointer we were looking for, we want to
                        // munge the pointer to point at the first element's pointer section.
                        ptr = ptr.offset(data_size as isize * BYTES_PER_WORD as isize);
                        if ptr_count == 0 {
                            return Err(Error::failed(
                                "Expected a pointer list, but got a list of data-only structs"
                                    .to_string(),
                            ));
                        }
                    }
                }

                Ok(ListReader {
                    arena,
                    segment_id,
                    cap_table,
                    ptr: ptr as *const _,
                    element_count: size,
                    element_size,
                    step: words_per_element * BITS_PER_WORD as u32,
                    struct_data_size: u32::from(data_size) * (BITS_PER_WORD as u32),
                    struct_pointer_count: ptr_count,
                    nesting_limit: nesting_limit - 1,
                })
            }
            _ => {
                // This is a primitive or pointer list, but all such lists can also be interpreted
                // as struct lists. We need to compute the data size and pointer count for such
                // structs.
                let data_size = data_bits_per_element((*reff).list_element_size());
                let pointer_count = pointers_per_element((*reff).list_element_size());
                let element_count = (*reff).list_element_count();
                let step = data_size + pointer_count * BITS_PER_POINTER as u32;

                let word_count = round_bits_up_to_words(u64::from(element_count) * u64::from(step));
                bounds_check(
                    arena,
                    segment_id,
                    ptr,
                    word_count as usize,
                    WirePointerKind::List,
                )?;

                if element_size == Void {
                    // Watch out for lists of void, which can claim to be arbitrarily large
                    // without having sent actual data.
                    amplified_read(arena, u64::from(element_count))?;
                }

                if let Some(expected_element_size) = expected_element_size {
                    if element_size == ElementSize::Bit && expected_element_size != ElementSize::Bit
                    {
                        return Err(Error::failed(
                            "Found bit list where struct list was expected; upgrade boolean lists to\
                             structs is no longer supported".to_string()));
                    }

                    // Verify that the elements are at least as large as the expected type. Note that if
                    // we expected InlineComposite, the expected sizes here will be zero, because bounds
                    // checking will be performed at field access time. So this check here is for the
                    // case where we expected a list of some primitive or pointer type.

                    let expected_data_bits_per_element =
                        data_bits_per_element(expected_element_size);
                    let expected_pointers_per_element = pointers_per_element(expected_element_size);

                    if expected_data_bits_per_element > data_size
                        || expected_pointers_per_element > pointer_count
                    {
                        return Err(Error::failed(
                            "Message contains list with incompatible element type.".to_string(),
                        ));
                    }
                }

                Ok(ListReader {
                    arena,
                    segment_id,
                    cap_table,
                    ptr: ptr as *const _,
                    element_count,
                    element_size,
                    step,
                    struct_data_size: data_size,
                    struct_pointer_count: pointer_count as u16,
                    nesting_limit: nesting_limit - 1,
                })
            }
        }
    }
