pub fn compress_with_flush<'a>(
    output: &'a mut [MaybeUninit<u8>],
    input: &[u8],
    config: DeflateConfig,
    final_flush: DeflateFlush,
) -> (&'a mut [u8], ReturnCode) {
    let mut stream = z_stream {
        next_in: input.as_ptr() as *mut u8,
        avail_in: 0, // for special logic in the first  iteration
        total_in: 0,
        next_out: output.as_mut_ptr() as *mut u8,
        avail_out: 0, // for special logic on the first iteration
        total_out: 0,
        msg: core::ptr::null_mut(),
        state: core::ptr::null_mut(),
        zalloc: None,
        zfree: None,
        opaque: core::ptr::null_mut(),
        data_type: 0,
        adler: 0,
        reserved: 0,
    };

    let err = init(&mut stream, config);
    if err != ReturnCode::Ok {
        return (&mut [], err);
    }

    let max = core::ffi::c_uint::MAX as usize;

    let mut left = output.len();
    let mut source_len = input.len();

    loop {
        if stream.avail_out == 0 {
            stream.avail_out = Ord::min(left, max) as _;
            left -= stream.avail_out as usize;
        }

        if stream.avail_in == 0 {
            stream.avail_in = Ord::min(source_len, max) as _;
            source_len -= stream.avail_in as usize;
        }

        let flush = if source_len > 0 {
            DeflateFlush::NoFlush
        } else {
            final_flush
        };

        let err = if let Some(stream) = unsafe { DeflateStream::from_stream_mut(&mut stream) } {
            deflate(stream, flush)
        } else {
            ReturnCode::StreamError
        };

        if err != ReturnCode::Ok {
            break;
        }
    }

    // SAFETY: we have now initialized these bytes
    let output_slice = unsafe {
        core::slice::from_raw_parts_mut(output.as_mut_ptr() as *mut u8, stream.total_out as usize)
    };

    // may DataError if insufficient output space
    let return_code = if let Some(stream) = unsafe { DeflateStream::from_stream_mut(&mut stream) } {
        match end(stream) {
            Ok(_) => ReturnCode::Ok,
            Err(_) => ReturnCode::DataError,
        }
    } else {
        ReturnCode::Ok
    };

    (output_slice, return_code)
}
