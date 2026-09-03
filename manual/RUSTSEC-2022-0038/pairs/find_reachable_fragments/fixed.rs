    fn find_reachable_fragments(&'a self, from: &Scope<'a>, result: &mut HashSet<&'a str>) {
        let mut to_visit = Vec::new();
        if let Scope::Fragment(name) = *from {
            to_visit.push(name);
        }

        while let Some(from) = to_visit.pop() {
            if let Some(next) = self.find_reachable_fragments_inner(from, result) {
                to_visit.extend(next);
            }
        }
    }
