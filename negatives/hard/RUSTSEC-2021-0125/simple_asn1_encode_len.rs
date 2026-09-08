fn encode_len(x: usize) -> Vec<u8> {
    if x < 128 {
        vec![x as u8]
    } else {
        let mut bstr = Vec::new();
        let mut work = x;

        // convert this into bytes, backwards
        while work > 0 {
            bstr.push(work as u8);
            work = work >> 8;
        }

        // encode the front of the length
        let len = bstr.len() as u8;
        bstr.push(len | 0x80);

        // and then reverse it into the right order
        bstr.reverse();
        bstr
    }
}
