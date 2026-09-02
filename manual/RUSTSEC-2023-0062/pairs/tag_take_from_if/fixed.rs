    pub fn take_from_if<S: Source>(
        self,
        source: &mut S,
    ) -> Result<Option<bool>, DecodeError<S::Error>> {
        if source.request(1)? == 0 {
            return Ok(None)
        }
        let byte = source.slice()[0];
        // clear constructed bit
        let mut data = [byte & !Tag::CONSTRUCTED_MASK, 0, 0, 0];
        if (data[0] & Tag::SINGLEBYTE_DATA_MASK) == Tag::SINGLEBYTE_DATA_MASK {
            let mut i = 1;
            loop {
                if source.request(i + 1)? <= i {
                    // Not enough data for a complete tag.
                    return Err(source.content_err("short tag value"))
                }
                data[i] = source.slice()[i];
                if data[i] & Tag::LAST_OCTET_MASK == 0 {
                    break
                }
                // We don’t support tags larger than 4 bytes.
                if i == 3 {
                    return Err(source.content_err(
                        "tag values longer than 4 bytes not implemented"
                    ))
                }
                i += 1;
            }
        }
        let (tag, constructed) = (
            Tag(data),
            byte & Tag::CONSTRUCTED_MASK != 0
        );
        if tag == self {
            source.advance(tag.encoded_len());
            Ok(Some(constructed))
        }
        else {
            Ok(None)
        }
    }
