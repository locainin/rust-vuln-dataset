pub unsafe fn emplace_scalar_array<T: EndianScalar, const N: usize>(
    buf: &mut [u8],
    loc: usize,
    src: &[T; N],
) {
    let mut buf_ptr = buf[loc..].as_mut_ptr();
    for item in src.iter() {
        let item_le = item.to_little_endian();
        core::ptr::copy_nonoverlapping(
            &item_le as *const T::Scalar as *const u8,
            buf_ptr,
            size_of::<T::Scalar>(),
        );
        buf_ptr = buf_ptr.add(size_of::<T::Scalar>());
    }
}
