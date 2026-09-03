    fn c_concat<'a, I>(&mut self, exprs: I) -> ResultOrEmpty
    where
        I: IntoIterator<Item = &'a Hir>,
    {
        let mut exprs = exprs.into_iter();
        let Patch { mut hole, entry } = loop {
            match exprs.next() {
                None => return self.c_empty(),
                Some(e) => {
                    if let Some(p) = self.c(e)? {
                        break p;
                    }
                }
            }
        };
        for e in exprs {
            if let Some(p) = self.c(e)? {
                self.fill(hole, p.entry);
                hole = p.hole;
            }
        }
        Ok(Some(Patch { hole: hole, entry: entry }))
    }
