    pub fn new(token: String, options: Option<SvixOptions>) -> Self {
        let base_path = options.and_then(|x| x.server_url).unwrap_or_else(|| {
            match token.split('.').last() {
                Some("us") => "https://api.us.svix.com",
                Some("eu") => "https://api.eu.svix.com",
                Some("in") => "https://api.in.svix.com",
                _ => "https://api.svix.com",
            }
            .to_string()
        });
        let cfg = Configuration {
            base_path,
            user_agent: Some(format!("svix-libs/{CRATE_VERSION}/rust")),
            bearer_access_token: Some(token),
            ..Configuration::default()
        };

        Self { cfg }
    }
