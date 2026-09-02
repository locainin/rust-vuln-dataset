    pub fn make_relative_path_current(&mut self, relative: &Path, delegate: &mut dyn Delegate) -> std::io::Result<()> {
        if self.valid_components != 0 && relative.as_os_str().is_empty() {
            return Err(std::io::Error::new(
                std::io::ErrorKind::Other,
                "empty inputs are not allowed",
            ));
        }
        if self.valid_components == 0 {
            delegate.push_directory(self)?;
        }

        let mut components = relative.components().peekable();
        let mut existing_components = self.current_relative.components();
        let mut matching_components = 0;
        while let (Some(existing_comp), Some(new_comp)) = (existing_components.next(), components.peek()) {
            if existing_comp == *new_comp {
                components.next();
                matching_components += 1;
            } else {
                break;
            }
        }

        for _ in 0..self.valid_components - matching_components {
            self.current.pop();
            self.current_relative.pop();
            if self.current_is_directory {
                delegate.pop_directory();
            }
            self.current_is_directory = true;
        }
        self.valid_components = matching_components;

        if !self.current_is_directory && components.peek().is_some() {
            delegate.push_directory(self)?;
        }

        while let Some(comp) = components.next() {
            if !matches!(comp, Component::Normal(_)) {
                return Err(std::io::Error::new(
                    std::io::ErrorKind::Other,
                    format!(
                        "Input path \"{}\" contains relative or absolute components",
                        relative.display()
                    ),
                ));
            }
            let is_last_component = components.peek().is_none();
            self.current_is_directory = !is_last_component;
            self.current.push(comp);
            self.current_relative.push(comp);
            self.valid_components += 1;
            let res = delegate.push(is_last_component, self);
            if self.current_is_directory {
                delegate.push_directory(self)?;
            }

            if let Err(err) = res {
                self.current.pop();
                self.current_relative.pop();
                self.valid_components -= 1;
                return Err(err);
            }
        }
        Ok(())
    }
