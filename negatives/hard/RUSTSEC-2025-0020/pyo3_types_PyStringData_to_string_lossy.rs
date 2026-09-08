    pub fn to_string_lossy(self) -> Cow<'a, str> {
        match self {
            Self::Ucs1(data) => String::from_utf8_lossy(data),
            Self::Ucs2(data) => Cow::Owned(String::from_utf16_lossy(data)),
            Self::Ucs4(data) => Cow::Owned(
                data.iter()
                    .map(|&c| std::char::from_u32(c).unwrap_or('\u{FFFD}'))
                    .collect(),
            ),
        }
    }
