    pub fn to_json(&self) -> serde_json::Value {
        json!({
            "name": self.name,
            "linesTotal": self.stats.total,
            "linesCovered": self.stats.covered,
            "linesMissed": self.stats.missed,
            "coveragePercent": self.stats.percent,
            "coverage": self.coverage,
        })
    }
