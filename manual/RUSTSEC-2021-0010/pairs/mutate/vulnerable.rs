#[inline]
pub fn mutate<T, F: FnOnce(T) -> T>(p: &mut T, f: F) { unsafe { ptr::write(p, f(ptr::read(p))) } }
