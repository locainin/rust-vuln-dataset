    fn from_bytes(mut bytes: &[u8]) -> Result<Self, BoxDynError> {
        let header = Header::try_read(&mut bytes)?;

        if bytes.len() != header.data_size() {
            return Err(DecodeError::new(
                &header,
                format!(
                    "expected {} bytes after header, got {}",
                    header.data_size(),
                    bytes.len()
                ),
            )
            .into());
        }

        match (header.is_point, header.dimensions) {
            (true, 1) => Ok(PgCube::Point(bytes.get_f64())),
            (true, _) => Ok(PgCube::ZeroVolume(
                read_vec(&mut bytes).map_err(|e| DecodeError::new(&header, e))?,
            )),
            (false, 1) => Ok(PgCube::OneDimensionInterval(
                bytes.get_f64(),
                bytes.get_f64(),
            )),
            (false, _) => Ok(PgCube::MultiDimension(read_cube(&header, bytes)?)),
        }
    }
