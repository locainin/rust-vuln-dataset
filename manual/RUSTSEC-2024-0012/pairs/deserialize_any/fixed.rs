    fn deserialize_any<V>(self, visitor: V) -> Result<V::Value>
    where
        V: Visitor<'de>,
    {
        match self.parse_whitespace().ok_or(Error::EofWhileParsingValue)? {
            b'n' => {
                self.eat_char();
                self.parse_ident(b"ull")?;
                visitor.visit_unit()
            }
            b't' => {
                self.eat_char();
                self.parse_ident(b"rue")?;
                visitor.visit_bool(true)
            }
            b'f' => {
                self.eat_char();
                self.parse_ident(b"alse")?;
                visitor.visit_bool(false)
            }
            b'-' => {
                deserialize_signed!(self, visitor, i64, visit_i64)
            }
            b'0'..=b'9' => {
                deserialize_unsigned!(self, visitor, u64, visit_u64)
            }
            b'"' => {
                self.eat_char();
                let str_like = self.parse_string()?;
                match str_like {
                    StringLike::Borrowed(str) => visitor.visit_borrowed_str(str),
                    StringLike::Owned(string) => visitor.visit_string(string),
                }
            }
            b'[' => {
                check_recursion! {
                    self.eat_char();
                    let ret = visitor.visit_seq(SeqAccess::new(self));
                }
                let ret = ret?;

                self.end_seq()?;

                Ok(ret)
            }
            b'{' => {
                check_recursion! {
                    self.eat_char();
                    let ret = visitor.visit_map(MapAccess::new(self));
                }
                let ret = ret?;

                self.end_map()?;

                Ok(ret)
            }
            _ => Err(Error::ExpectedSomeValue),
        }
    }
