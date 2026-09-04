    fn set_complete(cell: &AtomicUsize) -> State {
        // This method is a compare-and-swap loop rather than a fetch-or like
        // other `set_$WHATEVER` methods on `State`. This is because we must
        // check if the state has been closed before setting the `VALUE_SENT`
        // bit.
        //
        // We don't want to set both the `VALUE_SENT` bit if the `CLOSED`
        // bit is already set, because `VALUE_SENT` will tell the receiver that
        // it's okay to access the inner `UnsafeCell`. Immediately after calling
        // `set_complete`, if the channel was closed, the sender will _also_
        // access the `UnsafeCell` to take the value back out, so if a
        // `poll_recv` or `try_recv` call is occurring concurrently, both
        // threads may try to access the `UnsafeCell` if we were to set the
        // `VALUE_SENT` bit on a closed channel.
        let mut state = cell.load(Ordering::Relaxed);
        loop {
            if State(state).is_closed() {
                break;
            }
            // TODO: This could be `Release`, followed by an `Acquire` fence *if*
            // the `RX_TASK_SET` flag is set. However, `loom` does not support
            // fences yet.
            match cell.compare_exchange_weak(
                state,
                state | VALUE_SENT,
                Ordering::AcqRel,
                Ordering::Acquire,
            ) {
                Ok(_) => break,
                Err(actual) => state = actual,
            }
        }
        State(state)
    }
