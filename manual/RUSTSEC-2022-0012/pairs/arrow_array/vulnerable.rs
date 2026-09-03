#[repr(C)]
#[derive(Debug, Clone)]
pub struct ArrowArray {
    pub(super) length: i64,
    pub(super) null_count: i64,
    pub(super) offset: i64,
    pub(super) n_buffers: i64,
    pub(super) n_children: i64,
    pub(super) buffers: *mut *const ::std::os::raw::c_void,
    pub(super) children: *mut *mut ArrowArray,
    pub(super) dictionary: *mut ArrowArray,
    pub(super) release: ::std::option::Option<unsafe extern "C" fn(arg1: *mut ArrowArray)>,
    pub(super) private_data: *mut ::std::os::raw::c_void,
}
