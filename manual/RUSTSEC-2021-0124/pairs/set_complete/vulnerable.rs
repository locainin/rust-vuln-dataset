    fn set_complete(cell: &AtomicUsize) -> State {
        // TODO: This could be `Release`, followed by an `Acquire` fence *if*
        // the `RX_TASK_SET` flag is set. However, `loom` does not support
        // fences yet.
        let val = cell.fetch_or(VALUE_SENT, AcqRel);
        State(val)
    }
