unsafe fn context_drop_rest<D, E>(e: OwnedPtr<ErrorImpl<()>>, target: TypeId)
where
    D: 'static,
    E: 'static,
{
    // Called after downcasting by value to either the D or the E and doing a
    // ptr::read to take ownership of that value.
    if TypeId::of::<D>() == target {
        unsafe {
            e.cast::<ErrorImpl<ContextError<ManuallyDrop<D>, E>>>()
                .into_box()
        };
    } else {
        debug_assert_eq!(TypeId::of::<E>(), target);
        unsafe {
            e.cast::<ErrorImpl<ContextError<D, ManuallyDrop<E>>>>()
                .into_box()
        };
    }
}
