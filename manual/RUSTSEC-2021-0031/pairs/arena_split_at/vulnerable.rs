    pub fn split_at<'a, I: Borrow<Idx>>(
        &'a mut self,
        selected: I,
    ) -> Option<(&mut T, ArenaSplit<'a, T>)> {
        if let Some(value) = self.get_mut(selected.borrow()) {
            Some((
                unsafe { (value as *mut T).as_mut().unwrap() },
                ArenaSplit {
                    selected: selected.borrow().clone(),
                    arena: self,
                    __type: Default::default(),
                },
            ))
        } else {
            None
        }
    }
