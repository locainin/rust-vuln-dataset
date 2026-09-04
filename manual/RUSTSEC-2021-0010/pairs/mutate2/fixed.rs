#[inline]
pub fn mutate2<S, T, F: FnOnce(S, T) -> (S, T)>(p: &mut S, q: &mut T, f: F) { unsafe {
    let (x, y) = (ptr::read(p), ptr::read(q));
    let (x, y) = abort_on_unwind(move || f(x, y));
    ptr::write(p, x);
    ptr::write(q, y);
} }
