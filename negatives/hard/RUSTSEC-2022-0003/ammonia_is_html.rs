pub fn is_html(input: &str) -> bool {
    let santok = SanitizationTokenizer::new();
    let mut chunk = ByteTendril::new();
    chunk.push_slice(input.as_bytes());
    let mut input = BufferQueue::new();
    input.push_back(chunk.try_reinterpret().unwrap());

    let mut tok = Tokenizer::new(santok, Default::default());
    let _ = tok.feed(&mut input);
    tok.end();
    tok.sink.was_sanitized
}
