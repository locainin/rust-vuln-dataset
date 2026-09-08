    fn from_str(text: &str) -> Result<Self, Self::Err> {
        if text.is_empty() {
            return Err(Error::new(ErrorKind::Empty));
        }

        let mut pos = Position::Major;
        let (major, text) = numeric_identifier(text, pos)?;
        let text = dot(text, pos)?;

        pos = Position::Minor;
        let (minor, text) = numeric_identifier(text, pos)?;
        let text = dot(text, pos)?;

        pos = Position::Patch;
        let (patch, text) = numeric_identifier(text, pos)?;

        if text.is_empty() {
            return Ok(Version::new(major, minor, patch));
        }

        let (pre, text) = if let Some(text) = text.strip_prefix('-') {
            pos = Position::Pre;
            let (pre, text) = prerelease_identifier(text)?;
            if pre.is_empty() {
                return Err(Error::new(ErrorKind::EmptySegment(pos)));
            }
            (pre, text)
        } else {
            (Prerelease::EMPTY, text)
        };

        let (build, text) = if let Some(text) = text.strip_prefix('+') {
            pos = Position::Build;
            let (build, text) = build_identifier(text)?;
            if build.is_empty() {
                return Err(Error::new(ErrorKind::EmptySegment(pos)));
            }
            (build, text)
        } else {
            (BuildMetadata::EMPTY, text)
        };

        if let Some(unexpected) = text.chars().next() {
            return Err(Error::new(ErrorKind::UnexpectedCharAfter(pos, unexpected)));
        }

        Ok(Version {
            major,
            minor,
            patch,
            pre,
            build,
        })
    }
