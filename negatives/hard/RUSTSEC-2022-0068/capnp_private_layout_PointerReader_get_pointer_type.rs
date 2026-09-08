    pub fn get_pointer_type(&self) -> Result<PointerType> {
        if self.is_null() {
            Ok(PointerType::Null)
        } else {
            let (_, reff, _) =
                unsafe { wire_helpers::follow_fars(self.arena, self.pointer, self.segment_id)? };

            match unsafe { (*reff).kind() } {
                WirePointerKind::Far => {
                    Err(crate::Error::failed(String::from("Unexpected FAR pointer")))
                }
                WirePointerKind::Struct => Ok(PointerType::Struct),
                WirePointerKind::List => Ok(PointerType::List),
                WirePointerKind::Other => {
                    if unsafe { (*reff).is_capability() } {
                        Ok(PointerType::Capability)
                    } else {
                        Err(crate::Error::failed(String::from("Unknown pointer type")))
                    }
                }
            }
        }
    }
