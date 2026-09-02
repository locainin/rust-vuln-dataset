    pub fn from_content<S: decode::Source>(
        content: &mut decode::Content<S>
    ) -> Result<Self, DecodeError<S::Error>> {
        match *content {
            decode::Content::Primitive(ref mut inner) => {
                if inner.mode() == Mode::Cer && inner.remaining() > 1000 {
                    return Err(content.content_err(
                        "long bit string component in CER mode"
                    ))
                }
                let unused = inner.take_u8()?;
                if unused > 7 {
                    return Err(content.content_err(
                        "invalid bit string with large initial octet"
                    ));
                }
                if inner.remaining() == 0 && unused > 0 {
                    return Err(content.content_err(
                        "invalid bit string \
                         (non-zero initial with empty bits)"
                    ));
                }
                let bits = inner.take_all()?;

                // Strictly speaking, we should also check if the unused bits
                // in the last octet are zero.

                Ok(BitString { unused, bits })
            }
            decode::Content::Constructed(ref inner) => {
                if inner.mode() == Mode::Der {
                    Err(content.content_err(
                       "constructed bit string in DER mode"
                    ))
                }
                else {
                    Err(content.content_err(
                        "constructed bit string not implemented"
                    ))
                }
            }
        }
    }
