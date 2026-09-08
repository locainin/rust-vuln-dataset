pub fn ts_to_dt(ts: u64) -> Option<time::OffsetDateTime> {
    if ts == crate::UNDEF_TIMESTAMP {
        None
    } else {
        // u64::MAX is within maximum allowable range
        Some(time::OffsetDateTime::from_unix_timestamp_nanos(ts as i128).unwrap())
    }
}
