pub fn parse_response(response_status: StatusCode, body: Vec<u8>) -> Result<(), WebPushError> {
    if response_status.is_success() {
        return Ok(());
    }

    let info: ErrorInfo = serde_json::from_slice(&body).unwrap_or_else(|_| ErrorInfo {
        code: response_status.as_u16(),
        errno: 999,
        error: "unknown error".into(),
        message: String::from_utf8(body).unwrap_or_else(|_| "-".into()),
    });

    match response_status {
        StatusCode::UNAUTHORIZED => Err(WebPushError::Unauthorized(info)),
        StatusCode::GONE => Err(WebPushError::EndpointNotValid(info)),
        StatusCode::NOT_FOUND => Err(WebPushError::EndpointNotFound(info)),
        StatusCode::PAYLOAD_TOO_LARGE => Err(WebPushError::PayloadTooLarge),
        StatusCode::BAD_REQUEST => Err(WebPushError::BadRequest(info)),
        status if status.is_server_error() => Err(WebPushError::ServerError {
            retry_after: None,
            info,
        }),
        _ => Err(WebPushError::Other(info)),
    }
}
