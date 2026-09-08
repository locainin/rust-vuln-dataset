    fn deserialize_string<V>(self, visitor: V) -> Result<V::Value>
    where
        V: Visitor<'de>,
    {
        let peek = self.parse_whitespace().ok_or(Error::EofWhileParsingValue)?;

        match peek {
            b'"' => {
                self.eat_char();
                let str_like = self.parse_string()?;
                match str_like {
                    StringLike::Borrowed(str) => visitor.visit_borrowed_str(str),
                    StringLike::Owned(string) => visitor.visit_string(string),
                }
            }
            _ => Err(Error::InvalidType),
        }
    }
