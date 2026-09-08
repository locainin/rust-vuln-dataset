    pub(crate) fn line_to_err(&self, line: BString) -> Result<std::io::Error, BString> {
        let kind = match self {
            ProgramKind::Ssh | ProgramKind::Simple => {
                if line.contains_str(b"Permission denied") || line.contains_str(b"permission denied") {
                    Some(ErrorKind::PermissionDenied)
                } else if line.contains_str(b"resolve hostname") {
                    Some(ErrorKind::ConnectionRefused)
                } else if line.contains_str(b"connect to host")
                    || line.contains_str("Connection to ")
                    || line.contains_str("Connection closed by ")
                {
                    // TODO: turn this into HostUnreachable when stable, or NetworkUnreachable in 'no route' example.
                    //       It's important that it WON'T be considered spurious, but is considered a permanent failure.
                    Some(ErrorKind::NotFound)
                } else {
                    None
                }
            }
            ProgramKind::Plink | ProgramKind::Putty | ProgramKind::TortoisePlink => {
                if line.contains_str(b"publickey") {
                    Some(ErrorKind::PermissionDenied)
                } else {
                    None
                }
            }
        };
        match kind {
            Some(kind) => Ok(std::io::Error::new(kind, Vec::from(line).into_string_lossy())),
            None => Err(line),
        }
    }
