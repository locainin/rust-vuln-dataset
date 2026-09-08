    pub fn poll_closed(&mut self, cx: &mut Context<'_>) -> Poll<()> {
        // Keep track of task budget
        let coop = ready!(crate::coop::poll_proceed(cx));

        let inner = self.inner.as_ref().unwrap();

        let mut state = State::load(&inner.state, Acquire);

        if state.is_closed() {
            coop.made_progress();
            return Poll::Ready(());
        }

        if state.is_tx_task_set() {
            let will_notify = unsafe { inner.tx_task.will_wake(cx) };

            if !will_notify {
                state = State::unset_tx_task(&inner.state);

                if state.is_closed() {
                    // Set the flag again so that the waker is released in drop
                    State::set_tx_task(&inner.state);
                    coop.made_progress();
                    return Ready(());
                } else {
                    unsafe { inner.tx_task.drop_task() };
                }
            }
        }

        if !state.is_tx_task_set() {
            // Attempt to set the task
            unsafe {
                inner.tx_task.set_task(cx);
            }

            // Update the state
            state = State::set_tx_task(&inner.state);

            if state.is_closed() {
                coop.made_progress();
                return Ready(());
            }
        }

        Pending
    }
