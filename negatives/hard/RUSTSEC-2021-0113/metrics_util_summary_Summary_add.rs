    pub fn add(&mut self, value: f64) {
        if value.is_infinite() {
            return;
        }

        if value < self.min {
            self.min = value;
        }

        if value > self.max {
            self.max = value;
        }

        if value > self.min_value {
            self.positive.add(value);
        } else if value < -self.min_value {
            self.negative.add(-value);
        } else {
            self.zeroes += 1;
        }
    }
