    fn sub_self_call(
        &mut self, tptoken: TpToken, mut err_buffer: Vec<u8>,
        func: unsafe extern "C" fn(
            u64,
            *mut ydb_buffer_t,
            *const ydb_buffer_t,
            i32,
            *const ydb_buffer_t,
            *mut ydb_buffer_t,
        ) -> c_int,
    ) -> YDBResult<Vec<u8>> {
        let mut err_buffer_t = Self::make_out_buffer_t(&mut err_buffer);

        unsafe fn get_last_buffer(this: &mut Key) -> &mut Vec<u8> {
            // There is no performance difference, and using `or_else` causes a borrow-check error.
            #[allow(clippy::or_fun_call)]
            // SAFETY: This is only written to by `ydb_next_subscript` or `ydb_prev_subscript`, which only write variable names, not arbitrary data.
            // Since variable names are always ASCII, this is sound.
            this.subscripts.last_mut().unwrap_or(this.variable.as_mut_vec())
        };

        let status = loop {
            // NOTE: this can't be hoisted out of the loop because the variable or subscripts could be resized on INVSTRLEN.
            // WARNING: It's invalid for the unique reference returned by `get_last_buffer` to be
            // active at the same time that the variable or subscripts are being read from.
            // `last_self_buffer` only holds raw pointers, so it's ok for it not to be dropped
            // before calling `self.get_buffers()`.
            // NOTE: this is a purely compile time issue; the Rust compiler adds `noalias` to all
            // mut references. It can only go wrong from a miscompilation, not from a
            // use-after-free.
            let mut last_self_buffer = Key::make_out_buffer_t(unsafe { get_last_buffer(self) });

            // Get pointers to the varname and to the first subscript
            // NOTE: ideally this would only update the subscript or variable that changed in the previous loop iteration.
            // Without benchmarks, I'm not sure how much that would help performance, and this is simpler to work with.
            // This can't be moved outside the loop because the buffers could be resized on INVSTRLEN.
            let (varname, subscripts) = self.get_buffers();

            let status = unsafe {
                func(
                    tptoken.0,
                    &mut err_buffer_t,
                    varname.as_ptr(),
                    subscripts.len() as i32,
                    subscripts.as_ptr() as *const _,
                    &mut last_self_buffer,
                )
            };

            // See comments on `last_self_buffer` for why this has to be recalculated.
            let t = unsafe { get_last_buffer(self) };
            // If these are different, the `set_len` below is very wrong and will cause UB.
            assert_eq!(t.as_ptr() as *const _, last_self_buffer.buf_addr);

            // HACK: by looking at the source I saw that this only returns INVSTRLEN for variable or subscript,
            // not the error buffer (it will just write a shorter message).
            // So it's safe to only resize `t`.
            if status == YDB_ERR_INVSTRLEN {
                // From the docs for `reserve()`:
                // > After calling reserve, capacity will be greater than or equal to self.len() + additional
                t.reserve(last_self_buffer.len_used as usize - t.len());
                continue;
            }
            unsafe {
                t.set_len(min(last_self_buffer.len_alloc, last_self_buffer.len_used) as usize);
            }
            break status;
        };

        if status != YDB_OK as i32 {
            // Resize the vec with the buffer to we can see the value
            // We could end up with a buffer of a larger size if we couldn't fit the error string
            // into the out_buffer, so make sure to pick the smaller size
            unsafe {
                err_buffer.set_len(min(err_buffer_t.len_alloc, err_buffer_t.len_used) as usize);
            }
            // See https://gitlab.com/YottaDB/DB/YDB/-/issues/619
            debug_assert_ne!(status, YDB_ERR_TPRETRY);
            Err(YDBError { message: err_buffer, status, tptoken })
        } else {
            Ok(err_buffer)
        }
    }
