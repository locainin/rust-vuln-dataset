    pub fn external<'a, C, T>(cx: &mut C, data: T) -> Handle<'a, Self>
    where
        C: Context<'a>,
        T: AsMut<[u8]> + Send + 'static,
    {
        let env = cx.env().to_raw();
        let value = unsafe { neon_runtime::arraybuffer::new_external(env, data) };

        Handle::new_internal(Self(value))
    }
