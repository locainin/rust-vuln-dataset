    fn lookup_stack_map(&self, pc: usize) -> Option<&StackMap> {
        let text_offset = pc - self.start;
        let (index, func_offset) = self.module.func_by_text_offset(text_offset)?;
        let info = self.module.func_info(index);

        // Do a binary search to find the stack map for the given offset.
        let index = match info
            .stack_maps
            .binary_search_by_key(&func_offset, |i| i.code_offset)
        {
            // Found it.
            Ok(i) => i,

            // No stack map associated with this PC.
            //
            // Because we know we are in Wasm code, and we must be at some kind
            // of call/safepoint, then the Cranelift backend must have avoided
            // emitting a stack map for this location because no refs were live.
            #[cfg(not(feature = "old-x86-backend"))]
            Err(_) => return None,

            // ### Old x86_64 backend specific code.
            //
            // Because GC safepoints are technically only associated with a
            // single PC, we should ideally only care about `Ok(index)` values
            // returned from the binary search. However, safepoints are inserted
            // right before calls, and there are two things that can disturb the
            // PC/offset associated with the safepoint versus the PC we actually
            // use to query for the stack map:
            //
            // 1. The `backtrace` crate gives us the PC in a frame that will be
            //    *returned to*, and where execution will continue from, rather than
            //    the PC of the call we are currently at. So we would need to
            //    disassemble one instruction backwards to query the actual PC for
            //    the stack map.
            //
            //    TODO: One thing we *could* do to make this a little less error
            //    prone, would be to assert/check that the nearest GC safepoint
            //    found is within `max_encoded_size(any kind of call instruction)`
            //    our queried PC for the target architecture.
            //
            // 2. Cranelift's stack maps only handle the stack, not
            //    registers. However, some references that are arguments to a call
            //    may need to be in registers. In these cases, what Cranelift will
            //    do is:
            //
            //      a. spill all the live references,
            //      b. insert a GC safepoint for those references,
            //      c. reload the references into registers, and finally
            //      d. make the call.
            //
            //    Step (c) adds drift between the GC safepoint and the location of
            //    the call, which is where we actually walk the stack frame and
            //    collect its live references.
            //
            //    Luckily, the spill stack slots for the live references are still
            //    up to date, so we can still find all the on-stack roots.
            //    Furthermore, we do not have a moving GC, so we don't need to worry
            //    whether the following code will reuse the references in registers
            //    (which would not have been updated to point to the moved objects)
            //    or reload from the stack slots (which would have been updated to
            //    point to the moved objects).
            #[cfg(feature = "old-x86-backend")]
            Err(0) => return None,
            #[cfg(feature = "old-x86-backend")]
            Err(i) => i - 1,
        };

        Some(&info.stack_maps[index].stack_map)
    }
