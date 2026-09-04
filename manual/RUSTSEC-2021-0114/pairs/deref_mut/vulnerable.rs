impl DerefMut for TlsWyRand {
	/// Safety: [`TlsWyRand`] is neither [Send] nor [Sync], and thus,
	/// there will always be a thread-local [`WyRand`] when there is a [`TlsWyRand`]
	fn deref_mut(&mut self) -> &mut Self::Target {
		unsafe { &mut *(*self.0).get() }
	}
}
