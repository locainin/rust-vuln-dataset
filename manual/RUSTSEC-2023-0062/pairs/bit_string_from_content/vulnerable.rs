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
                Ok(BitString {
                    unused: inner.take_u8()?,
                    bits: inner.take_all()?,
                })
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
