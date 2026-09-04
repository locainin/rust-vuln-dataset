            fn set_label_type(&mut self, typ: LabelType) {
                assert!(!self.was_deleted());
                unsafe {
                    #set_label_type(self._inner, typ as i32);
                }
            }
