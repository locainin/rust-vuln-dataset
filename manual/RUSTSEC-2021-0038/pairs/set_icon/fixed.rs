            fn set_icon<T: ImageExt>(&mut self, image: Option<T>) {
                assert!(!self.was_deleted());
                assert!(std::any::type_name::<T>() != std::any::type_name::<crate::image::SharedImage>(), "SharedImage icons are not supported!");
                assert!(std::any::type_name::<T>() != std::any::type_name::<crate::image::Pixmap>(), "Pixmap icons are not supported!");
                assert!(std::any::type_name::<T>() != std::any::type_name::<crate::image::XpmImage>(), "Xpm icons are not supported!");
                assert!(std::any::type_name::<T>() != std::any::type_name::<crate::image::XbmImage>(), "Xbm icons are not supported!");
                assert!(std::any::type_name::<T>() != std::any::type_name::<crate::image::PnmImage>(), "Pnm icons are not supported!");
                assert!(std::any::type_name::<T>() != std::any::type_name::<crate::image::GifImage>(), "Gif icons are not supported!");
                assert!(std::any::type_name::<T>() != std::any::type_name::<crate::image::Image>(), "Icon images can't be generic!");
                let _old_image = self.image();
                if let Some(mut image) = image {
                    assert!(!image.was_deleted());
                    unsafe { image.increment_arc(); #set_icon(self._inner, image.as_image_ptr() as *mut _) }
                } else {
                    unsafe { #set_icon(self._inner, std::ptr::null_mut() as *mut raw::c_void) }
                }
            }
