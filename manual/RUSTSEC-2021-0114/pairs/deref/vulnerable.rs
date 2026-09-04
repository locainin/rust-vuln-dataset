impl Deref for TlsWyRand {
	type Target = WyRand;

	/// Safety: [`TlsWyRand`] is neither [Send] nor [Sync], and thus,
	/// there will always be a thread-local [`WyRand`] when there is a [`TlsWyRand`]
	fn deref(&self) -> &Self::Target {
		unsafe { &*self.0.get() }
	}
}
