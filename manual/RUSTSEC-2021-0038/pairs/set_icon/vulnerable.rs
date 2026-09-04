            fn set_icon<T: ImageExt>(&mut self, image: Option<T>) {
                assert!(!self.was_deleted());
                assert!(std::any::type_name::<T>() != std::any::type_name::<crate::image::SharedImage>(), "SharedImage icons are not supported!");
                let _old_image = self.image();
                if let Some(mut image) = image {
                    assert!(!image.was_deleted());
                    unsafe { image.increment_arc(); #set_icon(self._inner, image.as_image_ptr() as *mut _) }
                } else {
                    unsafe { #set_icon(self._inner, std::ptr::null_mut() as *mut raw::c_void) }
                }
            }
