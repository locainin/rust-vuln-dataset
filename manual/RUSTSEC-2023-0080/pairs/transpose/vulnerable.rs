pub fn transpose<T: Copy>(input: &[T], output: &mut [T], input_width: usize, input_height: usize) {
    assert_eq!(input_width*input_height, input.len());
    assert_eq!(input_width*input_height, output.len());
    if input.len() <= SMALL_LEN {
        unsafe { transpose_small(input, output, input_width, input_height) };
    }
    else if input.len() <= MEDIUM_LEN {
        transpose_tiled(input, output, input_width, input_height);
    }
    else {
        transpose_recursive(input, output, 0, input_height, 0, input_width, input_width, input_height);
    }
}
