fn chacha_quarter_round(state: &mut [u32; 16], a: usize, b: usize, c: usize, d: usize) {
	state[a] = state[a].wrapping_add(state[b]);
	state[d] ^= state[a];
	state[d] = state[d].rotate_left(16);

	state[c] = state[c].wrapping_add(state[d]);
	state[b] ^= state[c];
	state[b] = state[b].rotate_left(12);

	state[a] = state[a].wrapping_add(state[b]);
	state[d] ^= state[a];
	state[d] = state[d].rotate_left(8);

	state[c] = state[c].wrapping_add(state[d]);
	state[b] ^= state[c];
	state[b] = state[b].rotate_left(7);
}
