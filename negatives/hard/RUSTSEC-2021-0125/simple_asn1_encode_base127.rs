
fn encode_base127(v: &BigUint) -> Vec<u8> {
    let mut acc = v.clone();
    let mut res = Vec::new();
    let u128 = BigUint::from_u8(128).unwrap();
    let zero = BigUint::zero();

    if acc == zero {
        res.push(0);
        return res;
    }

    while acc > zero {
        // we build this vector backwards
        let digit = &acc % &u128;
        acc = acc >> 7;

        match digit.to_u8() {
            None => panic!("7 bits don't fit into 8, cause ..."),
            Some(x) if res.is_empty() => res.push(x),
            Some(x) => res.push(x | 0x80),
        }
    }

    res.reverse();
    res
}
