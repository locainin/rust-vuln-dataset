    pub(crate) async fn blocking_handler(
        self: Arc<Self>,
        request: Request<Body>,
        remote_addr: SocketAddr,
    ) -> Result<HyperResponse, ServiceError> {
        let (parts, body) = request.into_parts();
        let now = StartInstant::now();

        let full_body = hyper::body::to_bytes(body).await?;
        let request = Request::from_parts(parts, full_body);

        let handler = self.handler.clone();
        tokio::task::spawn_blocking(move || {
            let mut request = ConduitRequest::new(request, remote_addr, now);
            handler
                .call(&mut request)
                .map(conduit_into_hyper)
                .unwrap_or_else(|e| server_error_response(&e.to_string()))
        })
        .await
        .map_err(Into::into)
    }
