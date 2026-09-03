#[repr(C)]
#[derive(Debug)]
pub struct ArrowSchema {
    pub(super) format: *const ::std::os::raw::c_char,
    pub(super) name: *const ::std::os::raw::c_char,
    pub(super) metadata: *const ::std::os::raw::c_char,
    pub(super) flags: i64,
    pub(super) n_children: i64,
    pub(super) children: *mut *mut ArrowSchema,
    pub(super) dictionary: *mut ArrowSchema,
    pub(super) release: ::std::option::Option<unsafe extern "C" fn(arg1: *mut ArrowSchema)>,
    pub(super) private_data: *mut ::std::os::raw::c_void,
}
