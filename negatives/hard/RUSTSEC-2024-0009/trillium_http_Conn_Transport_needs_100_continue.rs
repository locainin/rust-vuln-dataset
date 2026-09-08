    fn needs_100_continue(&self) -> bool {
        self.request_body_state == ReceivedBodyState::Start
            && self.version != Version::Http1_0
            && self
                .request_headers
                .eq_ignore_ascii_case(Expect, "100-continue")
    }
