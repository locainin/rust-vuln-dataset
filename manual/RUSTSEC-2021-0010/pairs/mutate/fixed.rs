#[inline]
pub fn mutate<T, F: FnOnce(T) -> T>(p: &mut T, f: F) { unsafe {
    let x = ptr::read(p);
    let x = abort_on_unwind(move || f(x));
    ptr::write(p, x)
} }
