pub fn chacha_block<const ROUNDS: u8>(input: [u32; 16]) -> [u32; 16] {
	let mut x = input;
	assert_eq!(ROUNDS % 2, 0, "ChaCha rounds must be divisble by 2!");
	for _ in (0..ROUNDS).step_by(2) {
		// Odd rounds
		chacha_quarter_round(&mut x, 0, 4, 8, 12);
		chacha_quarter_round(&mut x, 1, 5, 9, 13);
		chacha_quarter_round(&mut x, 2, 6, 10, 14);
		chacha_quarter_round(&mut x, 3, 7, 11, 15);
		// Even rounds
		chacha_quarter_round(&mut x, 0, 5, 10, 15);
		chacha_quarter_round(&mut x, 1, 6, 11, 12);
		chacha_quarter_round(&mut x, 2, 7, 8, 13);
		chacha_quarter_round(&mut x, 3, 4, 9, 14);
	}
	x.iter_mut()
		.zip(input.iter())
		.for_each(|(l, r)| *l = l.wrapping_add(*r));
	x
}
