pub fn set_dictionary(stream: &mut InflateStream, dictionary: &[u8]) -> ReturnCode {
    if stream.state.wrap != 0 && !matches!(stream.state.mode, Mode::Dict) {
        return ReturnCode::StreamError;
    }

    // check for correct dictionary identifier
    if matches!(stream.state.mode, Mode::Dict) {
        let dictid = adler32(1, dictionary);

        if dictid != stream.state.checksum {
            return ReturnCode::DataError;
        }
    }

    let err = 'blk: {
        // initialize the window if needed
        if stream.state.window.size() == 0 {
            match Window::new_in(&stream.alloc, stream.state.wbits as usize) {
                None => break 'blk ReturnCode::MemError,
                Some(window) => stream.state.window = window,
            }
        }

        stream.state.window.extend(
            dictionary,
            stream.state.gzip_flags,
            false,
            &mut stream.state.checksum,
            &mut stream.state.crc_fold,
        );

        ReturnCode::Ok
    };

    if err != ReturnCode::Ok {
        stream.state.mode = Mode::Mem;
        return ReturnCode::MemError;
    }

    stream.state.flags.update(Flags::HAVE_DICT, true);

    ReturnCode::Ok
}
