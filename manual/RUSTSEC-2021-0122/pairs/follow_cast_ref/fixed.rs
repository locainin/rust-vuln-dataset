pub unsafe fn follow_cast_ref<'a, T: Sized + 'a>(buf: &'a [u8], loc: usize) -> &'a T {
    assert_eq!(align_of::<T>(), 1);
    let sz = size_of::<T>();
    let buf = &buf[loc..loc + sz];
    let ptr = buf.as_ptr() as *const T;
    // SAFETY
    // buf contains a value at loc of type T and T has no alignment requirements
    &*ptr
}
