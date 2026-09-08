pub fn timestamp_to_iso8601(ts: MilliSecondsSinceUnixEpoch) -> Option<String> {
    let nanos_since_epoch = i128::from(ts.get()) * 1_000_000;

    // OffsetDateTime has a max year of 9999, whereas MilliSecondsSinceUnixEpoch has
    // a max year of 285427, so `from_unix_timestamp_nanos` can overflow for very
    // large timestamps. (The Y10K problem!)
    let dt = OffsetDateTime::from_unix_timestamp_nanos(nanos_since_epoch).ok()?;

    // SAFETY: `format` can fail if:
    //   * The input lacks information on a component we have asked it to format
    //     (eg, it is given a `Time` and we ask it for a date), or
    //   * The input contains an invalid component (eg 30th February), or
    //   * An `io::Error` is raised internally.
    //
    // The first two cannot occur because we know we are giving it a valid
    // OffsetDateTime that has all the components we are asking it to print.
    //
    // The third should not occur because we are formatting a short string to an
    // in-memory buffer.

    Some(dt.format(&Iso8601::<ISO8601_WITH_MILLIS>).unwrap())
}
