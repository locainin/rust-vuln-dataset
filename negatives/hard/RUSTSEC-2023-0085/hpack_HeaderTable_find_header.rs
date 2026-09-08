    pub fn find_header(&self, header: (&[u8], &[u8])) -> Option<(usize, bool)> {
        // Just does a simple scan of the entire table, searching for a header
        // that matches both the name and the value of the given header.
        // If no such header is found, then any one of the headers that had a
        // matching name is returned, with the appropriate return flag set.
        //
        // The tables are so small that it is unlikely that the linear scan
        // would be a major performance bottlneck. If it does prove to be,
        // though, a more efficient lookup/header representation method could
        // be devised.
        let mut matching_name: Option<usize> = None;
        for (i, h) in self.iter().enumerate() {
            if header.0 == h.0 {
                if header.1 == h.1 {
                    // Both name and value matched: returns it immediately
                    return Some((i + 1, true));
                }
                // If only the name was valid, we continue scanning, hoping to
                // find one where both the name and value match. We remember
                // this one, in case such a header isn't found after all.
                matching_name = Some(i + 1);
            }
        }

        // Finally, if there's no header with a matching name and value,
        // return one that matched only the name, if that *was* found.
        match matching_name {
            Some(i) => Some((i, false)),
            None => None,
        }
    }
