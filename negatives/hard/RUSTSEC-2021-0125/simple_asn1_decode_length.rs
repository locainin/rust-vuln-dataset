fn decode_length(i: &[u8], index: &mut usize) -> Result<usize, ASN1DecodeErr> {
    if *index >= i.len() {
        return Err(ASN1DecodeErr::Incomplete);
    }
    let startbyte = i[*index];

    // NOTE: Technically, this size can be much larger than a usize.
    // However, our whole universe starts to break down if we get
    // things that big. So we're boring, and only accept lengths
    // that fit within a usize.
    *index += 1;
    if startbyte >= 0x80 {
        let mut lenlen = (startbyte & 0x7f) as usize;
        let mut res = 0;

        if lenlen > size_of::<usize>() {
            return Err(ASN1DecodeErr::LengthTooLarge(lenlen));
        }

        while lenlen > 0 {
            if *index >= i.len() {
                return Err(ASN1DecodeErr::Incomplete);
            }

            res = (res << 8) + (i[*index] as usize);

            *index += 1;
            lenlen -= 1;
        }

        Ok(res)
    } else {
        Ok(startbyte as usize)
    }
}
