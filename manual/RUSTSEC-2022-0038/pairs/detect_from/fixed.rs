    fn detect_from(&mut self, from: &'a str) {
        let mut to_visit = Vec::new();
        to_visit.push((from, Vec::new(), HashMap::new()));

        while let Some((from, path, path_indices)) = to_visit.pop() {
            to_visit.extend(self.detect_from_inner(from, path, path_indices));
        }
    }
