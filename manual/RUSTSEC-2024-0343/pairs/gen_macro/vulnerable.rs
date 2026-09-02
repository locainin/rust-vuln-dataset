#[macro_export]
macro_rules! gen {
    ($mod:tt, $len:tt, $alphabet:tt) => {
        #[doc = concat!(" Nanoid with alphabet table `", stringify!($alphabet), "`")]
        mod $mod {
            pub const MASK: usize = $len - 1;
            pub const ALPHABET: &'static [u8; $len] = $alphabet;
        }

        #[doc = concat!(" Nanoid with ", stringify!($mod))]
        #[must_use]
        pub fn $mod<const N: usize>() -> String {
            let mut bytes = [0u8; N];

            ::getrandom::getrandom(&mut bytes)
                .unwrap_or_else(|err| panic!("could not retreive random bytes: {err}"));

            bytes
                .iter_mut()
                .for_each(|b| *b = $mod::ALPHABET[*b as usize & $mod::MASK]);

            String::from_utf8_lossy(&bytes).to_string()
        }
    };
}
