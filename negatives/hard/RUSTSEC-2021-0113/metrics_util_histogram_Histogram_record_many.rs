    pub fn record_many<'a, S>(&mut self, samples: S)
    where
        S: IntoIterator<Item = &'a f64> + 'a,
    {
        let mut bucketed = vec![0u64; self.buckets.len()];

        let mut sum = 0.0;
        let mut count = 0;
        for sample in samples.into_iter() {
            sum += *sample;
            count += 1;

            for (idx, bucket) in self.bounds.iter().enumerate() {
                if sample <= bucket {
                    bucketed[idx] += 1;
                    break;
                }
            }
        }

        // Add each bucket to the next bucket to satisfy the "less than or equal to"
        // behavior of the buckets.
        if bucketed.len() >= 2 {
            for idx in 0..(bucketed.len() - 1) {
                bucketed[idx + 1] += bucketed[idx];
            }
        }

        // Merge our temporary buckets to our main buckets.
        for (idx, local) in bucketed.iter().enumerate() {
            self.buckets[idx] += local;
        }
        self.sum += sum;
        self.count += count;
    }
