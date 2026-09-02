#[doc(hidden)]
#[macro_export]
macro_rules! _covariant_access {
    (covariant, $Vis:vis, $Dependent:ident) => {
        /// Borrows dependent.
        $Vis fn borrow_dependent<'_q>(&'_q self) -> &'_q $Dependent<'_q> {
            fn _assert_covariance<'x: 'y, 'y>(x: $Dependent<'x>) -> $Dependent<'y> {
                //  This function only compiles for covariant types.
                x // Change the macro invocation to not_covariant.
            }

            unsafe { self.unsafe_self_cell.borrow_dependent() }
        }
    };
    (not_covariant, $Vis:vis, $Dependent:ident) => {
        // For types that are not covariant it's unsafe to allow
        // returning direct references.
        // For example a lifetime that is too short could be chosen:
        // See https://github.com/Voultapher/self_cell/issues/5
    };
    ($x:ident, $Vis:vis, $Dependent:ident) => {
        compile_error!("This macro only accepts `covariant` or `not_covariant`");
    };
}
