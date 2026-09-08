    fn poll_next(mut self: Pin<&mut Self>, cx: &mut Context) -> Poll<Option<Self::Item>> {
        let Self {
            ref mut file_range,
            ref mut range_iter,
            ref mut is_first_boundary,
            ref mut completed,
            ref boundary,
            ref content_type,
            file_length,
        } = *self;

        if *completed {
            return Poll::Ready(None);
        }

        if file_range.file_stream.remaining == 0 {
            let range = match range_iter.next() {
                Some(r) => r,
                None => {
                    *completed = true;

                    let header = render_multipart_header_end(boundary);
                    return Poll::Ready(Some(Ok(header.into())));
                }
            };

            file_range.seek_state = FileSeekState::NeedSeek;
            file_range.start_offset = range.start;
            file_range.file_stream.remaining = range.length;

            let cur_is_first = *is_first_boundary;
            *is_first_boundary = false;

            let header =
                render_multipart_header(boundary, content_type, range, cur_is_first, file_length);
            return Poll::Ready(Some(Ok(header.into())));
        }

        Pin::new(file_range).poll_next(cx)
    }
