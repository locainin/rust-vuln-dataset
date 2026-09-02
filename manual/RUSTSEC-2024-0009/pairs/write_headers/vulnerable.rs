    fn write_headers(&mut self, output_buffer: &mut Vec<u8>) -> std::io::Result<()> {
        use std::io::Write;
        let status = self.status().unwrap_or(Status::NotFound);

        write!(
            output_buffer,
            "{} {} {}\r\n",
            self.version,
            status as u16,
            status.canonical_reason()
        )?;

        self.finalize_headers();

        log::trace!(
            "sending:\n{} {}\n{}",
            self.version,
            status,
            &self.response_headers
        );

        for (header, values) in &self.response_headers {
            for value in values {
                write!(output_buffer, "{header}: ")?;
                output_buffer.extend_from_slice(value.as_ref());
                write!(output_buffer, "\r\n")?;
            }
        }

        write!(output_buffer, "\r\n")?;
        Ok(())
    }
