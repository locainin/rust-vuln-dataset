#[inline]
fn get_vtable_byte_len(field_locs: &[FieldLoc]) -> usize {
    let max_voffset = field_locs.iter().map(|fl| fl.id).max();
    match max_voffset {
        None => field_index_to_field_offset(0) as usize,
        Some(mv) => mv as usize + SIZE_VOFFSET,
    }
}
