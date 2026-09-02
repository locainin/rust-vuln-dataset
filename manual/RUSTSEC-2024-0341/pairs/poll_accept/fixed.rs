    pub fn poll_accept(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<<Self as Stream>::Item> {
        let mut this = self.project();

        loop {
            let mut empty_listener = false;
            for _ in 0..this.accept_batch_size.get() {
                match this.listener.as_mut().poll_accept(cx) {
                    Poll::Pending => {
                        empty_listener = true;
                        break;
                    }
                    Poll::Ready(Ok((conn, addr))) => {
                        this.waiting.push(Waiting {
                            inner: timeout(*this.timeout, this.tls.accept(conn)),
                            peer_addr: Some(addr),
                        });
                    }
                    Poll::Ready(Err(e)) => {
                        return Poll::Ready(Err(Error::ListenerError(e)));
                    }
                }
            }

            match this.waiting.poll_next_unpin(cx) {
                Poll::Ready(Some(result)) => return Poll::Ready(result),
                // If we don't have anything waiting yet,
                // then we are still pending,
                Poll::Ready(None) | Poll::Pending => {
                    if empty_listener {
                        return Poll::Pending;
                    }
                }
            }
        }
    }
