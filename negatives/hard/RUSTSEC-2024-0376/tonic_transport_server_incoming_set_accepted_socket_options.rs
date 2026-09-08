fn set_accepted_socket_options(stream: &TcpStream, nodelay: bool, keepalive: Option<Duration>) {
    if nodelay {
        if let Err(e) = stream.set_nodelay(true) {
            warn!("error trying to set TCP nodelay: {}", e);
        }
    }

    if let Some(timeout) = keepalive {
        let sock_ref = socket2::SockRef::from(&stream);
        let sock_keepalive = socket2::TcpKeepalive::new().with_time(timeout);

        if let Err(e) = sock_ref.set_tcp_keepalive(&sock_keepalive) {
            warn!("error trying to set TCP keepalive: {}", e);
        }
    }
}
