    pub fn build<F: IntoFileAccess>(
        &self,
        result: ResolveResult<F>,
    ) -> Result<Response<Body<F::Output>>> {
        match result {
            ResolveResult::MethodNotMatched => HttpResponseBuilder::new()
                .status(StatusCode::BAD_REQUEST)
                .body(Body::Empty),
            ResolveResult::NotFound => HttpResponseBuilder::new()
                .status(StatusCode::NOT_FOUND)
                .body(Body::Empty),
            ResolveResult::PermissionDenied => HttpResponseBuilder::new()
                .status(StatusCode::FORBIDDEN)
                .body(Body::Empty),
            ResolveResult::IsDirectory {
                redirect_to: mut target,
            } => {
                // Preserve any query string from the original request.
                if let Some(query) = self.query {
                    target.push('?');
                    target.push_str(query);
                }

                HttpResponseBuilder::new()
                    .status(StatusCode::MOVED_PERMANENTLY)
                    .header(header::LOCATION, target)
                    .body(Body::Empty)
            }
            ResolveResult::Found(file) => self.file_response_builder.build(file),
        }
    }
