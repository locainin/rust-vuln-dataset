fn conduit_into_hyper(response: ConduitResponse) -> HyperResponse {
    use conduit::Body::*;

    let (parts, body) = response.into_parts();
    let body = match body {
        Static(slice) => slice.into(),
        Owned(vec) => vec.into(),
        File(file) => FileStream::from_std(file).into_streamed_body(),
    };
    HyperResponse::from_parts(parts, body)
}
