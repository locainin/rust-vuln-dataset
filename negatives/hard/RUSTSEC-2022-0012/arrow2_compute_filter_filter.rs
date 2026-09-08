pub fn filter(array: &dyn Array, filter: &BooleanArray) -> Result<Box<dyn Array>> {
    // The validities may be masking out `true` bits, making the filter operation
    // based on the values incorrect
    if let Some(validities) = filter.validity() {
        let values = filter.values();
        let new_values = values & validities;
        let filter = BooleanArray::from_data(DataType::Boolean, new_values, None);
        return crate::compute::filter::filter(array, &filter);
    }

    use crate::datatypes::PhysicalType::*;
    match array.data_type().to_physical_type() {
        Primitive(primitive) => with_match_primitive_type!(primitive, |$T| {
            let array = array.as_any().downcast_ref().unwrap();
            Ok(Box::new(filter_primitive::<$T>(array, filter)))
        }),
        _ => {
            let iter = SlicesIterator::new(filter.values());
            let mut mutable = make_growable(&[array], false, iter.slots());
            iter.for_each(|(start, len)| mutable.extend(0, start, len));
            Ok(mutable.as_box())
        }
    }
}
