  pub(crate) fn trigger(&self, event: &str, window: Option<String>, payload: Option<String>) {
    let mut maybe_pending = false;
    match self.inner.handlers.try_lock() {
      Err(_) => self.insert_pending(Pending::Trigger(event.to_owned(), window, payload)),
      Ok(lock) => {
        if let Some(handlers) = lock.get(event) {
          for (&id, handler) in handlers {
            if handler.window.is_none() || window == handler.window {
              maybe_pending = true;
              (handler.callback)(self::Event {
                id,
                data: payload.clone(),
              })
            }
          }
        }
      }
    }

    if maybe_pending {
      self.flush_pending();
    }
  }
