    fn try_from(value: u8) -> Result<Self, Self::Error> {
        Ok(match value {
            0x81 => MsgType::InitHello,
            0x82 => MsgType::RespHello,
            0x83 => MsgType::InitConf,
            0x84 => MsgType::EmptyData,
            0x85 => MsgType::DataMsg,
            0x86 => MsgType::CookieReply,
            _ => return Err(RosenpassError::InvalidMessageType(value)),
        })
    }
