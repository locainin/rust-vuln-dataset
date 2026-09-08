fn server_error_response(message: &str) -> HyperResponse {
    error!("Internal Server Error: {}", message);
    let body = hyper::Body::from("Internal Server Error");
    Response::builder()
        .status(StatusCode::INTERNAL_SERVER_ERROR)
        .body(body)
        .expect("Unexpected invalid header")
}
