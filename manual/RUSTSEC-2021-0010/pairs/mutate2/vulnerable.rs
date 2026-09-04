#[inline]
pub fn mutate2<S, T, F: FnOnce(S, T) -> (S, T)>(p: &mut S, q: &mut T, f: F) { unsafe {
    let (x, y) = f(ptr::read(p), ptr::read(q));
    ptr::write(p, x);
    ptr::write(q, y);
} }
