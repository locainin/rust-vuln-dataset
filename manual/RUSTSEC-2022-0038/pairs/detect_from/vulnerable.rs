    fn detect_from(&mut self, from: &'a str, path: &mut Vec<&'a Spanning<&'a str>>) {
        self.visited.insert(from);

        if !self.spreads.contains_key(from) {
            return;
        }

        self.path_indices.insert(from, path.len());

        for node in &self.spreads[from] {
            let name = &node.item;
            let index = self.path_indices.get(name).cloned();

            if let Some(index) = index {
                let err_pos = if index < path.len() {
                    path[index]
                } else {
                    node
                };

                self.errors
                    .push(RuleError::new(&error_message(name), &[err_pos.start]));
            } else if !self.visited.contains(name) {
                path.push(node);
                self.detect_from(name, path);
                path.pop();
            }
        }

        self.path_indices.remove(from);
    }
