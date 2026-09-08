fn try_parse_rfc_850(time: &str) -> Option<PrimitiveDateTime> {
    let dt = PrimitiveDateTime::parse(time, "%A, %d-%b-%y %H:%M:%S").ok()?;

    // If the `time` string contains a two-digit year, then as per RFC 2616 § 19.3,
    // we consider the year as part of this century if it's within the next 50 years,
    // otherwise we consider as part of the previous century.

    let now = OffsetDateTime::now_utc();
    let century_start_year = (now.year() / 100) * 100;
    let mut expanded_year = century_start_year + dt.year();

    if expanded_year > now.year() + 50 {
        expanded_year -= 100;
    }

    let date = Date::try_from_ymd(expanded_year, dt.month(), dt.day()).ok()?;
    Some(PrimitiveDateTime::new(date, dt.time()))
}
