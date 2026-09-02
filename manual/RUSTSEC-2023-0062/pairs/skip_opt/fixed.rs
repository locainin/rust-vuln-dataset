    pub fn skip_opt<F>(
        &mut self, mut op: F,
    ) -> Result<Option<()>, DecodeError<S::Error>>
    where F: FnMut(Tag, bool, usize) -> Result<(), ContentError> {
        // If we already know we are at the end of the value, we can return.
        if self.is_exhausted() {
            return Ok(None)
        }

        // The stack for unrolling the recursion. For each level, we keep the
        // limit the source should be set to when the value ends. For
        // indefinite values, we keep `None`.
        let mut stack = SmallVec::<[Option<Option<usize>>; 4]>::new();

        loop {
            // Get a the ‘header’ of a value.
            let (tag, constructed) = Tag::take_from(self.source)?;
            let length = Length::take_from(self.source, self.mode)?;

            if !constructed {
                if tag == Tag::END_OF_VALUE {
                    if length != Length::Definite(0) {
                        return Err(self.content_err("non-empty end of value"))
                    }

                    // End-of-value: The top of the stack needs to be an
                    // indefinite value for it to be allowed. If it is, pop
                    // that value off the stack and continue. The limit is
                    // still that from the value one level above.
                    match stack.pop() {
                        Some(None) => { }
                        None => {
                            // We read end-of-value as the very first value.
                            // This can only happen if the outer value is
                            // an indefinite value. If so, change state and
                            // return.
                            if self.state == State::Indefinite {
                                self.state = State::Done;
                                return Ok(None)
                            }
                            else {
                                return Err(self.content_err(
                                    "invalid nested values"
                                ))
                            }
                        }
                        _ => {
                            return Err(self.content_err(
                                "invalid nested values"
                            ))
                        }
                    }
                }
                else {
                    // Primitive value. Check for the length to be definite,
                    // check that the caller likes it, then try to read over
                    // it.
                    if let Length::Definite(len) = length {
                        if let Err(err) = op(tag, constructed, stack.len()) {
                            return Err(self.content_err(err));
                        }
                        if self.source.request(len)? < len {
                            return Err(self.content_err(
                                "short primitive value"
                            ))
                        }
                        self.source.advance(len);
                    }
                    else {
                        return Err(self.content_err(
                            "primitive value with indefinite length"
                        ))
                    }
                }
            }
            else if let Length::Definite(len) = length {
                // Definite constructed value. First check if the caller
                // likes it. Check that there is enough limit left for the
                // value. If so, push the limit at the end of the value to
                // the stack, update the limit to our length, and continue.
                if let Err(err) = op(tag, constructed, stack.len()) {
                    return Err(self.content_err(err));
                }
                stack.push(Some(match self.source.limit() {
                    Some(limit) => {
                        match limit.checked_sub(len) {
                            Some(len) => Some(len),
                            None => {
                                return Err(self.content_err(
                                    "invalid nested values"
                                ));
                            }
                        }
                    }
                    None => None,
                }));
                self.source.set_limit(Some(len));
            }
            else {
                // Indefinite constructed value. Simply push a `None` to the
                // stack, if the caller likes it.
                if let Err(err) = op(tag, constructed, stack.len()) {
                    return Err(self.content_err(err));
                }
                stack.push(None);
                continue;
            }

            // Now we need to check if we have reached the end of a
            // constructed value. This happens if the limit of the
            // source reaches 0. Since the ends of several stacked values
            // can align, we need to loop here. Also, if we run out of
            // stack, we are done.
            loop {
                if stack.is_empty() {
                    return Ok(Some(()))
                }
                else if self.source.limit() == Some(0) {
                    match stack.pop() {
                        Some(Some(limit)) => {
                            self.source.set_limit(limit)
                        }
                        Some(None) => {
                            // We need a End-of-value, so running out of
                            // data is an error.
                            return Err(self.content_err("
                                missing further values"
                            ))
                        }
                        None => unreachable!(),
                    }
                }
                else {
                    break;
                }
            }

        }
    }
