    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        let mut this = self.project();
        let res = ready!(this.inner.as_mut().poll(cx));
        let addr = this
            .peer_addr
            .take()
            .expect("this future has already been polled to completion");
        match res {
            // We succesfully got a connection
            Ok(Ok(conn)) => Poll::Ready(Ok((conn, addr))),
            // The handshake failed
            Ok(Err(e)) => Poll::Ready(Err(Error::TlsAcceptError {
                error: e,
                peer_addr: addr,
            })),
            // The handshake timed out
            Err(_) => Poll::Ready(Err(Error::HandshakeTimeout { peer_addr: addr })),
        }
    }
