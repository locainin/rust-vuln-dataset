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

        // Get pointers to the varname and to the first subscript
        let (varname, subscripts) = self.get_buffers();
        let t = self.subscripts.last_mut().unwrap_or(unsafe { self.variable.as_mut_vec() });
        let mut last_self_buffer;
        let status = loop {
            last_self_buffer = ydb_buffer_t {
                buf_addr: t.as_mut_ptr() as *mut _,
                len_alloc: t.capacity() as u32,
                len_used: t.len() as u32,
            };

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
            // HACK: by looking at the source I saw that this only returns INVSTRLEN for variable or subscript,
            // not the error buffer (it will just write a shorter message).
            // So it's safe to only resize `t`.
            if status == YDB_ERR_INVSTRLEN {
                // New size should be size needed + (current size - len used)
                let new_size = (last_self_buffer.len_used - last_self_buffer.len_alloc) as usize;
                let new_size = new_size + (t.capacity() - t.len());
                t.reserve(new_size);
                continue;
            }
            break status;
        };
        // Resize the vec with the buffer to we can see the value
        // We could end up with a buffer of a larger size if we couldn't fit the error string
        // into the out_buffer, so make sure to pick the smaller size
        if status != YDB_OK as i32 {
            unsafe {
                err_buffer.set_len(min(err_buffer_t.len_alloc, err_buffer_t.len_used) as usize);
            }
            // See https://gitlab.com/YottaDB/DB/YDB/-/issues/619
            debug_assert_ne!(status, YDB_ERR_TPRETRY);
            return Err(YDBError { message: err_buffer, status, tptoken });
        }
        unsafe {
            t.set_len(min(last_self_buffer.len_alloc, last_self_buffer.len_used) as usize);
        }
        Ok(err_buffer)
    }
