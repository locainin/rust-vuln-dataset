    #[inline]
    fn deserialize<R: std::io::Read>(
        mut reader: &mut R,
        version_map: &VersionMap,
        app_version: u16,
    ) -> VersionizeResult<Self> {
        let len = usize::deserialize(&mut reader, version_map, app_version)?;
        // Even if we fail in serialize, we still need to enforce this on the hot path
        // in case the len is corrupted.
        if len > MAX_STRING_LEN {
            return Err(VersionizeError::StringLength(len));
        }

        let mut v = vec![0u8; len];
        reader
            .read_exact(v.as_mut_slice())
            .map_err(|e| VersionizeError::Io(e.raw_os_error().unwrap_or(0)))?;
        String::from_utf8(v)
            .map_err(|err| VersionizeError::Deserialize(format!("Utf8 error: {:?}", err)))
    }
