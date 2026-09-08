    pub fn userids(&self) -> impl Iterator<Item=UserID> + '_
    {
        self.packets()
            .filter_map(|p| {
                if p.tag() == Tag::UserID {
                    UserID::try_from(p.body()).ok()
                } else {
                    None
                }
            })
    }
