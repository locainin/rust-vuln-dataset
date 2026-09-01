    pub fn accept(
        &mut self,
        mut incoming: Incoming,
        now: Instant,
        buf: &mut Vec<u8>,
        server_config: Option<Arc<ServerConfig>>,
    ) -> Result<(ConnectionHandle, Connection), AcceptError> {
        let remote_address_validated = incoming.remote_address_validated();
        incoming.improper_drop_warner.dismiss();
        let incoming_buffer = self.incoming_buffers.remove(incoming.incoming_idx);
        self.all_incoming_buffers_total_bytes -= incoming_buffer.total_bytes;

        let packet_number = incoming.packet.header.number.expand(0);
        let InitialHeader {
            src_cid,
            dst_cid,
            version,
            ..
        } = incoming.packet.header;

        if self.cids_exhausted() {
            debug!("refusing connection");
            self.index.remove_initial(dst_cid);
            return Err(AcceptError {
                cause: ConnectionError::CidsExhausted,
                response: Some(self.initial_close(
                    version,
                    incoming.addresses,
                    &incoming.crypto,
                    &src_cid,
                    TransportError::CONNECTION_REFUSED(""),
                    buf,
                )),
            });
        }

        let server_config =
            server_config.unwrap_or_else(|| self.server_config.as_ref().unwrap().clone());

        if incoming
            .crypto
            .packet
            .remote
            .decrypt(
                packet_number,
                &incoming.packet.header_data,
                &mut incoming.packet.payload,
            )
            .is_err()
        {
            debug!(packet_number, "failed to authenticate initial packet");
            self.index.remove_initial(dst_cid);
            return Err(AcceptError {
                cause: TransportError::PROTOCOL_VIOLATION("authentication failed").into(),
                response: None,
            });
        };

        let ch = ConnectionHandle(self.connections.vacant_key());
        let loc_cid = self.new_cid(ch);
        let mut params = TransportParameters::new(
            &server_config.transport,
            &self.config,
            self.local_cid_generator.as_ref(),
            loc_cid,
            Some(&server_config),
        );
        params.stateless_reset_token = Some(ResetToken::new(&*self.config.reset_key, &loc_cid));
        params.original_dst_cid = Some(incoming.orig_dst_cid);
        params.retry_src_cid = incoming.retry_src_cid;
        let mut pref_addr_cid = None;
        if server_config.preferred_address_v4.is_some()
            || server_config.preferred_address_v6.is_some()
        {
            let cid = self.new_cid(ch);
            pref_addr_cid = Some(cid);
            params.preferred_address = Some(PreferredAddress {
                address_v4: server_config.preferred_address_v4,
                address_v6: server_config.preferred_address_v6,
                connection_id: cid,
                stateless_reset_token: ResetToken::new(&*self.config.reset_key, &cid),
            });
        }

        let tls = server_config.crypto.clone().start_session(version, &params);
        let transport_config = server_config.transport.clone();
        let mut conn = self.add_connection(
            ch,
            version,
            dst_cid,
            loc_cid,
            src_cid,
            pref_addr_cid,
            incoming.addresses,
            now,
            tls,
            Some(server_config),
            transport_config,
            remote_address_validated,
        );
        self.index.insert_initial(dst_cid, ch);

        match conn.handle_first_packet(
            now,
            incoming.addresses.remote,
            incoming.ecn,
            packet_number,
            incoming.packet,
            incoming.rest,
        ) {
            Ok(()) => {
                trace!(id = ch.0, icid = %dst_cid, "new connection");

                for event in incoming_buffer.datagrams {
                    conn.handle_event(ConnectionEvent(ConnectionEventInner::Datagram(event)))
                }

                Ok((ch, conn))
            }
            Err(e) => {
                debug!("handshake failed: {}", e);
                self.handle_event(ch, EndpointEvent(EndpointEventInner::Drained));
                let response = match e {
                    ConnectionError::TransportError(ref e) => Some(self.initial_close(
                        version,
                        incoming.addresses,
                        &incoming.crypto,
                        &src_cid,
                        e.clone(),
                        buf,
                    )),
                    _ => None,
                };
                Err(AcceptError { cause: e, response })
            }
        }
    }
