    fn eq(&self, v2: &OID) -> bool {
        let &&OID(ref vec1) = self;
        let &OID(ref vec2) = v2;

        if vec1.len() != vec2.len() {
            return false;
        }

        for i in 0..vec1.len() {
            if vec1[i] != vec2[i] {
                return false;
            }
        }

        true
    }
