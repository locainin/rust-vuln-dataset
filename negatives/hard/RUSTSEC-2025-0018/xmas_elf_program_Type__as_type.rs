    fn as_type(&self) -> Result<Type, &'static str> {
        match self.0 {
            0 => Ok(Type::Null),
            1 => Ok(Type::Load),
            2 => Ok(Type::Dynamic),
            3 => Ok(Type::Interp),
            4 => Ok(Type::Note),
            5 => Ok(Type::ShLib),
            6 => Ok(Type::Phdr),
            7 => Ok(Type::Tls),
            TYPE_GNU_RELRO => Ok(Type::GnuRelro),
            t if (TYPE_LOOS..=TYPE_HIOS).contains(&t) => Ok(Type::OsSpecific(t)),
            t if (TYPE_LOPROC..=TYPE_HIPROC).contains(&t) => Ok(Type::ProcessorSpecific(t)),
            _ => Err("Invalid type"),
        }
    }
