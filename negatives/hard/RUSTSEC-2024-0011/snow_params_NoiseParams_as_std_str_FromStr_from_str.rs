    #[cfg(not(feature = "hfs"))]
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let mut split = s.split('_');
        Ok(NoiseParams::new(
            s.to_owned(),
            split.next().ok_or(PatternProblem::TooFewParameters)?.parse()?,
            split.next().ok_or(PatternProblem::TooFewParameters)?.parse()?,
            split.next().ok_or(PatternProblem::TooFewParameters)?.parse()?,
            split.next().ok_or(PatternProblem::TooFewParameters)?.parse()?,
            split.next().ok_or(PatternProblem::TooFewParameters)?.parse()?,
        ))
    }
