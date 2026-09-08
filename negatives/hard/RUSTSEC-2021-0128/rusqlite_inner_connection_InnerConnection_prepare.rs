    pub fn prepare<'a>(&mut self, conn: &'a Connection, sql: &str) -> Result<Statement<'a>> {
        let mut c_stmt = ptr::null_mut();
        let (c_sql, len, _) = str_for_sqlite(sql.as_bytes())?;
        let mut c_tail = ptr::null();
        let r = unsafe {
            if cfg!(feature = "unlock_notify") {
                let mut rc;
                loop {
                    rc = ffi::sqlite3_prepare_v2(
                        self.db(),
                        c_sql,
                        len,
                        &mut c_stmt as *mut *mut ffi::sqlite3_stmt,
                        &mut c_tail as *mut *const c_char,
                    );
                    if !unlock_notify::is_locked(self.db, rc) {
                        break;
                    }
                    rc = unlock_notify::wait_for_unlock_notify(self.db);
                    if rc != ffi::SQLITE_OK {
                        break;
                    }
                }
                rc
            } else {
                ffi::sqlite3_prepare_v2(
                    self.db(),
                    c_sql,
                    len,
                    &mut c_stmt as *mut *mut ffi::sqlite3_stmt,
                    &mut c_tail as *mut *const c_char,
                )
            }
        };
        // If there is an error, *ppStmt is set to NULL.
        self.decode_result(r)?;
        // If the input text contains no SQL (if the input is an empty string or a
        // comment) then *ppStmt is set to NULL.
        let c_stmt: *mut ffi::sqlite3_stmt = c_stmt;
        let c_tail: *const c_char = c_tail;
        let tail = if c_tail.is_null() {
            0
        } else {
            let n = (c_tail as isize) - (c_sql as isize);
            if n <= 0 || n >= len as isize {
                0
            } else {
                n as usize
            }
        };
        Ok(Statement::new(conn, unsafe {
            RawStatement::new(c_stmt, tail)
        }))
    }
