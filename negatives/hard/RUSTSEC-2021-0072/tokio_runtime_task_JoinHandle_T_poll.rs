    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        let mut ret = Poll::Pending;

        // Keep track of task budget
        let coop = ready!(crate::coop::poll_proceed(cx));

        // Raw should always be set. If it is not, this is due to polling after
        // completion
        let raw = self
            .raw
            .as_ref()
            .expect("polling after `JoinHandle` already completed");

        // Try to read the task output. If the task is not yet complete, the
        // waker is stored and is notified once the task does complete.
        //
        // The function must go via the vtable, which requires erasing generic
        // types. To do this, the function "return" is placed on the stack
        // **before** calling the function and is passed into the function using
        // `*mut ()`.
        //
        // Safety:
        //
        // The type of `T` must match the task's output type.
        unsafe {
            raw.try_read_output(&mut ret as *mut _ as *mut (), cx.waker());
        }

        if ret.is_ready() {
            coop.made_progress();
        }

        ret
    }
