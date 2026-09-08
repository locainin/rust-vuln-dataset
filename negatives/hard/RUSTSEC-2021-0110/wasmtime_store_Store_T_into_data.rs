    pub fn into_data(mut self) -> T {
        // This is an unsafe operation because we want to avoid having a runtime
        // check or boolean for whether the data is actually contained within a
        // `Store`. The data itself is stored as `ManuallyDrop` since we're
        // manually managing the memory here, and there's also a `ManuallyDrop`
        // around the `Box<StoreInner<T>>`. The way this works though is a bit
        // tricky, so here's how things get dropped appropriately:
        //
        // * When a `Store<T>` is normally dropped, the custom destructor for
        //   `Store<T>` will drop `T`, then the `self.inner` field. The
        //   rustc-glue destructor runs for `Box<StoreInner<T>>` which drops
        //   `StoreInner<T>`. This cleans up all internal fields and doesn't
        //   touch `T` because it's wrapped in `ManuallyDrop`.
        //
        // * When calling this method we skip the top-level destructor for
        //   `Store<T>` with `mem::forget`. This skips both the destructor for
        //   `T` and the destructor for `StoreInner<T>`. We do, however, run the
        //   destructor for `Box<StoreInner<T>>` which, like above, will skip
        //   the destructor for `T` since it's `ManuallyDrop`.
        //
        // In both cases all the other fields of `StoreInner<T>` should all get
        // dropped, and the manual management of destructors is basically
        // between this method and `Drop for Store<T>`. Note that this also
        // means that `Drop for StoreInner<T>` cannot access `self.data`, so
        // there is a comment indicating this as well.
        unsafe {
            let mut inner = ManuallyDrop::take(&mut self.inner);
            std::mem::forget(self);
            ManuallyDrop::take(&mut inner.data)
        }
    }
