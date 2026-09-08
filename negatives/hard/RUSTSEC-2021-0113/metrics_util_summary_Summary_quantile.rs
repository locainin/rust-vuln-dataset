    pub fn quantile(&self, q: f64) -> Option<f64> {
        if q < 0.0 || q > 1.0 || self.count() == 0 {
            return None;
        }

        let ncount = self.negative.count();
        let pcount = self.positive.count();
        let zcount = self.zeroes;
        let total = ncount + pcount + zcount;
        let rank = (q * (total - 1) as f64) as usize;

        if rank < ncount {
            // Quantile lands in the negative side.
            let nq = 1.0 - (rank as f64 / ncount as f64);
            self.negative
                .quantile(nq)
                .expect("quantile should be valid at this point")
                .map(|v| -v)
        } else if rank >= ncount && rank < (ncount + zcount) {
            // Quantile lands in the zero band.
            Some(0.0)
        } else {
            // Quantile lands in the positive side.
            let pq = (rank - (ncount + zcount)) as f64 / pcount as f64;
            self.positive
                .quantile(pq)
                .expect("quantile should be valid at this point")
        }
    }
