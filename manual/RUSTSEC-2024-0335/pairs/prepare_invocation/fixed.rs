    pub(crate) fn prepare_invocation(
        &self,
        ssh_cmd: &OsStr,
        url: &gix_url::Url,
        desired_version: Protocol,
        disallow_shell: bool,
    ) -> Result<gix_command::Prepare, ssh::invocation::Error> {
        let mut prepare = gix_command::prepare(ssh_cmd).with_shell();
        if disallow_shell {
            prepare.use_shell = false;
        }
        match self {
            ProgramKind::Ssh => {
                if desired_version != Protocol::V1 {
                    prepare = prepare
                        .args(["-o", "SendEnv=GIT_PROTOCOL"])
                        .env("GIT_PROTOCOL", format!("version={}", desired_version as usize))
                }
                if let Some(port) = url.port {
                    prepare = prepare.arg(format!("-p{port}"));
                }
            }
            ProgramKind::Plink | ProgramKind::Putty | ProgramKind::TortoisePlink => {
                if *self == ProgramKind::TortoisePlink {
                    prepare = prepare.arg("-batch");
                }
                if let Some(port) = url.port {
                    prepare = prepare.arg("-P");
                    prepare = prepare.arg(port.to_string());
                }
            }
            ProgramKind::Simple => {
                if url.port.is_some() {
                    return Err(ssh::invocation::Error::Unsupported {
                        command: ssh_cmd.into(),
                        function: "setting the port",
                    });
                }
            }
        };
        let host_maybe_with_user_as_ssh_arg = match url.user() {
            Some(user) => {
                // FIXME: See the fixme comment on Url::user_argument_safe() about its return type.
                if url.user_argument_safe() != Some(user) {
                    return Err(ssh::invocation::Error::AmbiguousUserName { user: user.into() });
                }
                let host = url.host().expect("present in ssh urls");
                format!("{user}@{host}")
            }
            None => {
                let host = url
                    .host_argument_safe()
                    .ok_or_else(|| ssh::invocation::Error::AmbiguousHostName {
                        host: url.host().expect("ssh host always set").into(),
                    })?;
                host.into()
            }
        };

        // Try to force ssh to yield English messages (for parsing later).
        Ok(prepare
            .arg(host_maybe_with_user_as_ssh_arg)
            .env("LANG", "C")
            .env("LC_ALL", "C"))
    }
