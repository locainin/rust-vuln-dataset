    fn parse(s: &str) -> Result<Self, BoxError> {
        let mut s = String::from(s);
        if s.ends_with(" -0000") {
            // The httpdate crate expects the `Date` to end in ` GMT`, but email
            // uses `-0000`, so we crudely fix this issue here.

            s.truncate(s.len() - "-0000".len());
            s.push_str("GMT");
        }

        Ok(Self(s.parse::<HttpDate>()?))
    }
