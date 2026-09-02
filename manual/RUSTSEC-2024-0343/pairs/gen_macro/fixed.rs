#[macro_export]
macro_rules! gen {
    ($mod:tt, $len:tt, $alphabet:tt) => {
        #[doc = concat!(" Nanoid with alphabet table `", stringify!($alphabet), "`")]
        mod $mod {
            pub const MASK: usize = ($len as usize).next_power_of_two() - 1;
            pub const ALPHABET: &'static [u8; $len] = $alphabet;
        }

        #[doc = concat!(" Nanoid with ", stringify!($mod))]
        #[must_use]
        pub fn $mod<const N: usize>() -> String {
            let mut bytes = vec![0u8; 8 * N / 5];
            let mut id = String::with_capacity(N);

            loop {
                ::getrandom::getrandom(&mut bytes)
                    .unwrap_or_else(|err| panic!("could not retreive random bytes: {err}"));

                for byte in &bytes {
                    let idx = *byte as usize & $mod::MASK;
                    if idx < $len {
                        id.push($mod::ALPHABET[idx] as char)
                    }
                    if id.len() == N {
                        return id;
                    }
                }
            }
        }
    };
}
