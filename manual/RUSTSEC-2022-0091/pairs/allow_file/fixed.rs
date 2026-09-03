  pub fn allow_file<P: AsRef<Path>>(&self, path: P) -> crate::Result<()> {
    let path = path.as_ref();
    push_pattern(
      &mut self.allowed_patterns.lock().unwrap(),
      &path,
      escaped_pattern,
    )?;
    self.trigger(Event::PathAllowed(path.to_path_buf()));
    Ok(())
  }
