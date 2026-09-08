    pub fn anchorize(&mut self, header: String) -> String {
        lazy_static! {
            static ref REJECTED_CHARS: Regex = Regex::new(r"[^\p{L}\p{M}\p{N}\p{Pc} -]").unwrap();
        }

        let mut id = header;
        id = id.to_lowercase();
        id = REJECTED_CHARS.replace_all(&id, "").to_string();
        id = id.replace(' ', "-");

        let mut uniq = 0;
        id = loop {
            let anchor = if uniq == 0 {
                Cow::from(&*id)
            } else {
                Cow::from(format!("{}-{}", &id, uniq))
            };

            if !self.0.contains(&*anchor) {
                break anchor.to_string();
            }

            uniq += 1;
        };
        self.0.insert(id.clone());
        id
    }
