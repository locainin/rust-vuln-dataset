fn handle_accept_error(e: impl Into<crate::Error>) -> ControlFlow<crate::Error> {
    let e = e.into();
    tracing::debug!(error = %e, "accept loop error");
    if let Some(e) = e.downcast_ref::<io::Error>() {
        if matches!(
            e.kind(),
            io::ErrorKind::ConnectionAborted
                | io::ErrorKind::Interrupted
                | io::ErrorKind::InvalidData // Raised if TLS handshake failed
                | io::ErrorKind::WouldBlock
        ) {
            return ControlFlow::Continue(());
        }
    }

    ControlFlow::Break(e)
}
