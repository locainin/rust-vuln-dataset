fn encode_tag(c: ASN1Class, constructed: bool, t: &BigUint) -> Vec<u8> {
    let cbyte = encode_class(c);

    match t.to_u8() {
        Some(mut x) if x < 31 => {
            if constructed {
                x |= 0b0010_0000;
            }
            vec![cbyte | x]
        }
        _ => {
            let mut res = encode_base127(t);
            let mut x = cbyte | 0b0001_1111;
            if constructed {
                x |= 0b0010_0000;
            }
            res.insert(0, x);
            res
        }
    }
}
