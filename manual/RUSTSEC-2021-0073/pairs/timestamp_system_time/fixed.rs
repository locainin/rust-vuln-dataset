    fn try_from(mut timestamp: Timestamp) -> Result<std::time::SystemTime, Self::Error> {
        let orig_timestamp = timestamp.clone();
        timestamp.normalize();

        let system_time = if timestamp.seconds >= 0 {
            std::time::UNIX_EPOCH.checked_add(time::Duration::from_secs(timestamp.seconds as u64))
        } else {
            std::time::UNIX_EPOCH
                .checked_sub(time::Duration::from_secs((-timestamp.seconds) as u64))
        };

        let system_time = system_time.and_then(|system_time| {
            system_time.checked_add(time::Duration::from_nanos(timestamp.nanos as u64))
        });

        system_time.ok_or(TimestampOutOfSystemRangeError {
            timestamp: orig_timestamp,
        })
    }
