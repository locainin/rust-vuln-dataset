  pub fn allow_directory<P: AsRef<Path>>(&self, path: P, recursive: bool) -> crate::Result<()> {
    let path = path.as_ref();
    {
      let mut list = self.allowed_patterns.lock().unwrap();

      // allow the directory to be read
      push_pattern(&mut list, &path, escaped_pattern)?;
      // allow its files and subdirectories to be read
      push_pattern(&mut list, &path, |p| {
        escaped_pattern_with(p, if recursive { "**" } else { "*" })
      })?;
    }
    self.trigger(Event::PathAllowed(path.to_path_buf()));
    Ok(())
  }
