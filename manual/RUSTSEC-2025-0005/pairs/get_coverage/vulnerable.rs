    fn get_coverage(coverage: BTreeMap<u32, u64>) -> (usize, usize, Vec<i64>) {
        let mut covered = 0;
        let last_line = *coverage.keys().last().unwrap_or(&0) as usize;
        let total = coverage.len();
        let mut lines: Vec<i64> = vec![-1; last_line];
        for (line_num, line_count) in coverage.iter() {
            let line_count = *line_count;
            unsafe {
                *lines.get_unchecked_mut((*line_num - 1) as usize) = line_count as i64;
            }
            covered += (line_count > 0) as usize;
        }
        (total, covered, lines)
    }
