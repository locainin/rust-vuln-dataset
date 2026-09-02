    fn deserialize_enum<V>(
        self,
        _name: &'static str,
        _variants: &'static [&'static str],
        visitor: V,
    ) -> Result<V::Value>
    where
        V: Visitor<'de>,
    {
        match self.parse_whitespace().ok_or(Error::EofWhileParsingValue)? {
            // if it is a string enum
            b'"' => visitor.visit_enum(UnitVariantAccess::new(self)),
            // if it is a struct enum
            b'{' => {
                check_recursion! {
                    self.eat_char();
                    let value = visitor.visit_enum(StructVariantAccess::new(self));
                }
                value
            }
            _ => Err(Error::ExpectedSomeIdent),
        }
    }
