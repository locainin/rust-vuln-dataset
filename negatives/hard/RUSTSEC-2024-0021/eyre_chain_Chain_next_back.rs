    fn next_back(&mut self) -> Option<Self::Item> {
        match &mut self.state {
            Linked { mut next } => {
                let mut rest = Vec::new();
                while let Some(cause) = next {
                    next = cause.source();
                    rest.push(cause);
                }
                let mut rest = rest.into_iter();
                let last = rest.next_back();
                self.state = Buffered { rest };
                last
            }
            Buffered { rest } => rest.next_back(),
        }
    }
