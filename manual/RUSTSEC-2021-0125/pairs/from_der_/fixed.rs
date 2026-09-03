fn from_der_(i: &[u8], start_offset: usize) -> Result<Vec<ASN1Block>, ASN1DecodeErr> {
    let mut result: Vec<ASN1Block> = Vec::new();
    let mut index: usize = 0;
    let len = i.len();

    while index < len {
        let soff = start_offset + index;
        let (tag, constructed, class) = decode_tag(i, &mut index)?;
        let len = decode_length(i, &mut index)?;
        let checklen = index
            .checked_add(len)
            .ok_or(ASN1DecodeErr::LengthTooLarge(len))?;
        if checklen > i.len() {
            return Err(ASN1DecodeErr::Incomplete);
        }
        let body = &i[index..(index + len)];

        if class != ASN1Class::Universal {
            if constructed {
                // Try to read as explicitly tagged
                match from_der_(body, start_offset + index) {
                    Ok(mut items) => {
                        if items.len() == 1 {
                            result.push(ASN1Block::Explicit(
                                class,
                                soff,
                                tag,
                                Box::new(items.remove(0)),
                            ));
                            index += len;
                            continue;
                        }
                    }
                    Err(_) => {}
                }
            }
            result.push(ASN1Block::Unknown(
                class,
                constructed,
                soff,
                tag,
                body.to_vec(),
            ));
            index += len;
            continue;
        }

        // Universal class
        match tag.to_u8() {
            // BOOLEAN
            Some(0x01) => {
                if len != 1 {
                    return Err(ASN1DecodeErr::BadBooleanLength(len));
                }
                result.push(ASN1Block::Boolean(soff, body[0] != 0));
            }
            // INTEGER
            Some(0x02) => {
                let res = BigInt::from_signed_bytes_be(&body);
                result.push(ASN1Block::Integer(soff, res));
            }
            // BIT STRING
            Some(0x03) if body.len() == 0 => result.push(ASN1Block::BitString(soff, 0, Vec::new())),
            Some(0x03) => {
                let bits = (&body[1..]).to_vec();
                let bitcount = bits.len() * 8;
                let rest = body[0] as usize;
                if bitcount < rest {
                    return Err(ASN1DecodeErr::InvalidBitStringLength(
                        bitcount as isize - rest as isize,
                    ));
                }

                let nbits = bitcount - (body[0] as usize);
                result.push(ASN1Block::BitString(soff, nbits, bits))
            }
            // OCTET STRING
            Some(0x04) => result.push(ASN1Block::OctetString(soff, body.to_vec())),
            // NULL
            Some(0x05) => {
                result.push(ASN1Block::Null(soff));
            }
            // OBJECT IDENTIFIER
            Some(0x06) => {
                let mut value1 = BigUint::zero();
                if body.len() == 0 {
                    return Err(ASN1DecodeErr::Incomplete);
                }
                let mut value2 = BigUint::from_u8(body[0]).unwrap();
                let mut oidres = Vec::new();
                let mut bindex = 1;

                if body[0] >= 40 {
                    if body[0] < 80 {
                        value1 = BigUint::one();
                        value2 = value2 - BigUint::from_u8(40).unwrap();
                    } else {
                        value1 = BigUint::from_u8(2).unwrap();
                        value2 = value2 - BigUint::from_u8(80).unwrap();
                    }
                }

                oidres.push(value1);
                oidres.push(value2);
                while bindex < body.len() {
                    oidres.push(decode_base127(body, &mut bindex)?);
                }
                let res = OID(oidres);

                result.push(ASN1Block::ObjectIdentifier(soff, res))
            }
            // UTF8STRING
            Some(0x0C) => match String::from_utf8(body.to_vec()) {
                Ok(v) => result.push(ASN1Block::UTF8String(soff, v)),
                Err(e) => return Err(ASN1DecodeErr::UTF8DecodeFailure(e.utf8_error())),
            },
            // SEQUENCE
            Some(0x10) => match from_der_(body, start_offset + index) {
                Ok(items) => result.push(ASN1Block::Sequence(soff, items)),
                Err(e) => return Err(e),
            },
            // SET
            Some(0x11) => match from_der_(body, start_offset + index) {
                Ok(items) => result.push(ASN1Block::Set(soff, items)),
                Err(e) => return Err(e),
            },
            // PRINTABLE STRING
            Some(0x13) => {
                let mut res = String::new();
                let val = body.iter().map(|x| *x as char);

                for c in val {
                    if PRINTABLE_CHARS.contains(c) {
                        res.push(c);
                    } else {
                        return Err(ASN1DecodeErr::PrintableStringDecodeFailure);
                    }
                }
                result.push(ASN1Block::PrintableString(soff, res));
            }
            // TELETEX STRINGS
            Some(0x14) => match String::from_utf8(body.to_vec()) {
                Ok(v) => result.push(ASN1Block::TeletexString(soff, v)),
                Err(e) => return Err(ASN1DecodeErr::UTF8DecodeFailure(e.utf8_error())),
            },
            // IA5 (ASCII) STRING
            Some(0x16) => {
                let val = body.iter().map(|x| *x as char);
                let res = String::from_iter(val);
                result.push(ASN1Block::IA5String(soff, res))
            }
            // UTCTime
            Some(0x17) => {
                if body.len() != 13 {
                    return Err(ASN1DecodeErr::InvalidDateValue(format!("{}", body.len())));
                }

                let v = String::from_iter(body.iter().map(|x| *x as char));

                let y = match v.get(0..2) {
                    Some(yy) => yy,
                    None => {
                        // This wasn't a valid character boundrary.
                        return Err(ASN1DecodeErr::InvalidDateValue(v));
                    }
                };

                let y_prefix = match y.parse::<u8>() {
                    Err(_) => return Err(ASN1DecodeErr::InvalidDateValue(v)),
                    Ok(y) => {
                        if y >= 50 {
                            "19"
                        } else {
                            "20"
                        }
                    }
                };

                let v = format!("{}{}", y_prefix, v);

                let format = time::format_description::parse(
                    "[year][month][day][hour repr:24][minute][second]Z",
                )
                .unwrap();

                match PrimitiveDateTime::parse(&v, &format) {
                    Err(_) => return Err(ASN1DecodeErr::InvalidDateValue(v)),
                    Ok(t) => result.push(ASN1Block::UTCTime(soff, t)),
                }
            }
            // GeneralizedTime
            Some(0x18) => {
                if body.len() < 15 {
                    return Err(ASN1DecodeErr::InvalidDateValue(format!("{}", body.len())));
                }

                let mut v: String = String::from_utf8(body.to_vec())
                    .map_err(|e| ASN1DecodeErr::UTF8DecodeFailure(e.utf8_error()))?;
                // Make sure the string is ascii, otherwise we cannot insert
                // chars at specific bytes.
                if !v.is_ascii() {
                    return Err(ASN1DecodeErr::InvalidDateValue(v));
                }

                // We need to add padding back to the string if it's not there.
                if !v.contains('.') {
                    v.insert(14, '.')
                }
                while v.len() < 25 {
                    let idx = v.len() - 1;
                    v.insert(idx, '0');
                }

                let format = time::format_description::parse(
                    "[year][month][day][hour repr:24][minute][second].[subsecond]Z",
                )
                .unwrap();

                match PrimitiveDateTime::parse(&v, &format) {
                    Err(_) => return Err(ASN1DecodeErr::InvalidDateValue(v)),
                    Ok(t) => result.push(ASN1Block::GeneralizedTime(soff, t)),
                }
            }
            // UNIVERSAL STRINGS
            Some(0x1C) => match String::from_utf8(body.to_vec()) {
                Ok(v) => result.push(ASN1Block::UniversalString(soff, v)),
                Err(e) => return Err(ASN1DecodeErr::UTF8DecodeFailure(e.utf8_error())),
            },
            // UNIVERSAL STRINGS
            Some(0x1E) => match String::from_utf8(body.to_vec()) {
                Ok(v) => result.push(ASN1Block::BMPString(soff, v)),
                Err(e) => return Err(ASN1DecodeErr::UTF8DecodeFailure(e.utf8_error())),
            },
            // Dunno.
            _ => {
                result.push(ASN1Block::Unknown(
                    class,
                    constructed,
                    soff,
                    tag,
                    body.to_vec(),
                ));
            }
        }
        index += len;
    }

    if result.is_empty() {
        Err(ASN1DecodeErr::EmptyBuffer)
    } else {
        Ok(result)
    }
}
