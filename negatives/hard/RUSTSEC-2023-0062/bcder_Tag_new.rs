    #[inline]
    fn new(class_mask: u8, number: u32) -> Self {
        assert!(number <= Tag::MAX_VAL_SPAN_3_OCTETS);
        if number <= Tag::MAX_VAL_FOURTH_OCTET {
            Tag([class_mask | number as u8, 0, 0, 0])
        } else if number <= Tag::MAX_VAL_SPAN_1_OCTET {
            // Fit the number in the third octets
            let number = number as u8;
            Tag([class_mask | Tag::SINGLEBYTE_DATA_MASK, number, 0, 0])
        } else if number <= Tag::MAX_VAL_SPAN_2_OCTETS {
            // Fit the number in the second and the third octets
            let first_part = {
                Tag::MULTIBYTE_DATA_MASK & ((number >> 7) as u8)
                | Tag::LAST_OCTET_MASK
            };
            let second_part = Tag::MULTIBYTE_DATA_MASK & (number as u8);
            Tag([
                class_mask | Tag::SINGLEBYTE_DATA_MASK, first_part,
                second_part, 0
            ])
        } else {
            // Fit the number in the first, second and the third octets
            let first_part = {
                Tag::MULTIBYTE_DATA_MASK & ((number >> 14) as u8)
                | Tag::LAST_OCTET_MASK
            };
            let second_part = {
                Tag::MULTIBYTE_DATA_MASK & ((number >> 7) as u8)
                | Tag::LAST_OCTET_MASK
            };
            let third_part = Tag::MULTIBYTE_DATA_MASK & (number as u8);
            Tag([
                class_mask | Tag::SINGLEBYTE_DATA_MASK, first_part,
                second_part, third_part
            ])
        }
    }
