    fn process_next_value<F, T>(
        &mut self,
        expected: Option<Tag>,
        op: F
    ) -> Result<Option<T>, DecodeError<S::Error>>
    where
        F: FnOnce(Tag, &mut Content<S>) -> Result<T, DecodeError<S::Error>>
    {
        if self.is_exhausted() {
            return Ok(None)
        }
        let (tag, constructed) = if let Some(expected) = expected {
            (
                expected,
                match expected.take_from_if(self.source)? {
                    Some(compressed) => compressed,
                    None => return Ok(None)
                }
            )
        }
        else {
            Tag::take_from(self.source)?
        };
        let length = Length::take_from(self.source, self.mode)?;

        if tag == Tag::END_OF_VALUE {
            if let State::Indefinite = self.state {
                if constructed {
                    return Err(self.source.content_err(
                        "constructed end of value"
                    ))
                }
                if !length.is_zero() {
                    return Err(self.source.content_err(
                        "non-empty end of value"
                    ))
                }
                self.state = State::Done;
                return Ok(None)
            }
            else {
                return Err(self.source.content_err(
                    "unexpected end of value"
                ))
            }
        }

        match length {
            Length::Definite(len) => {
                if let Some(limit) = self.source.limit() {
                    if len > limit {
                        return Err(self.source.content_err(
                            "nested value with excessive length"
                        ))
                    }
                }
                let old_limit = self.source.limit_further(Some(len));
                let res = {
                    let mut content = if constructed {
                        // Definite length constructed values are not allowed
                        // in CER.
                        if self.mode == Mode::Cer {
                            return Err(self.source.content_err(
                                "definite length constructed in CER mode"
                            ))
                        }
                        Content::Constructed(
                            Constructed::new(
                                self.source, State::Definite, self.mode
                            )
                        )
                    }
                    else {
                        Content::Primitive(
                            Primitive::new(self.source, self.mode)
                        )
                    };
                    let res = op(tag, &mut content)?;
                    content.exhausted()?;
                    res
                };
                self.source.set_limit(old_limit.map(|x| x - len));
                Ok(Some(res))
            }
            Length::Indefinite => {
                if !constructed || self.mode == Mode::Der {
                    return Err(self.source.content_err(
                        "indefinite length constructed in DER mode"
                    ))
                }
                let mut content = Content::Constructed(
                    Constructed::new(
                        self.source, State::Indefinite, self.mode
                    )
                );
                let res = op(tag, &mut content)?;
                content.exhausted()?;
                Ok(Some(res))
            }
        }
    }
