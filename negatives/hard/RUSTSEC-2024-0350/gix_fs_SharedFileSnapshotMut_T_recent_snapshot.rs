    pub fn recent_snapshot<E>(
        &self,
        mut current_modification_time: impl FnMut() -> Option<std::time::SystemTime>,
        open: impl FnOnce() -> Result<Option<T>, E>,
    ) -> Result<Option<SharedFileSnapshot<T>>, E> {
        let state = get_ref(self);
        let recent_modification = current_modification_time();
        let buffer = match (&*state, recent_modification) {
            (None, None) => (*state).clone(),
            (Some(_), None) => {
                drop(state);
                let mut state = get_mut(self);
                *state = None;
                (*state).clone()
            }
            (Some(snapshot), Some(modified_time)) => {
                if snapshot.modified < modified_time {
                    drop(state);
                    let mut state = get_mut(self);

                    if let (Some(_snapshot), Some(modified_time)) = (&*state, current_modification_time()) {
                        *state = open()?.map(|value| {
                            OwnShared::new(FileSnapshot {
                                value,
                                modified: modified_time,
                            })
                        });
                    }

                    (*state).clone()
                } else {
                    // Note that this relies on sub-section precision or else is a race when the packed file was just changed.
                    // It's nothing we can know though, so… up to the caller unfortunately.
                    Some(snapshot.clone())
                }
            }
            (None, Some(_modified_time)) => {
                drop(state);
                let mut state = get_mut(self);
                // Still in the same situation? If so, load the buffer. This compensates for the trampling herd
                // during lazy-loading at the expense of another mtime check.
                if let (None, Some(modified_time)) = (&*state, current_modification_time()) {
                    *state = open()?.map(|value| {
                        OwnShared::new(FileSnapshot {
                            value,
                            modified: modified_time,
                        })
                    });
                }
                (*state).clone()
            }
        };
        Ok(buffer)
    }
