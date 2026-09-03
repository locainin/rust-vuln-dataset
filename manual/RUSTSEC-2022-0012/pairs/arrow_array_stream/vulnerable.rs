#[repr(C)]
#[derive(Debug, Clone)]
pub struct ArrowArrayStream {
    pub(super) get_schema: ::std::option::Option<
        unsafe extern "C" fn(
            arg1: *mut ArrowArrayStream,
            out: *mut ArrowSchema,
        ) -> ::std::os::raw::c_int,
    >,
    pub(super) get_next: ::std::option::Option<
        unsafe extern "C" fn(
            arg1: *mut ArrowArrayStream,
            out: *mut ArrowArray,
        ) -> ::std::os::raw::c_int,
    >,
    pub(super) get_last_error: ::std::option::Option<
        unsafe extern "C" fn(arg1: *mut ArrowArrayStream) -> *const ::std::os::raw::c_char,
    >,
    pub(super) release: ::std::option::Option<unsafe extern "C" fn(arg1: *mut ArrowArrayStream)>,
    pub(super) private_data: *mut ::std::os::raw::c_void,
}
