    pub fn new_empty(data_type: &DataType) -> Self {
        let buffers = new_buffers(data_type, 0);
        let [buffer1, buffer2] = buffers;
        let buffers = into_buffers(data_type, buffer1, buffer2);

        let child_data = match data_type {
            DataType::Null
            | DataType::Boolean
            | DataType::UInt8
            | DataType::UInt16
            | DataType::UInt32
            | DataType::UInt64
            | DataType::Int8
            | DataType::Int16
            | DataType::Int32
            | DataType::Int64
            | DataType::Float32
            | DataType::Float64
            | DataType::Date32
            | DataType::Date64
            | DataType::Time32(_)
            | DataType::Time64(_)
            | DataType::Duration(_)
            | DataType::Timestamp(_, _)
            | DataType::Utf8
            | DataType::Binary
            | DataType::LargeUtf8
            | DataType::LargeBinary
            | DataType::Interval(_)
            | DataType::FixedSizeBinary(_)
            | DataType::Decimal(_, _) => vec![],
            DataType::List(field) => {
                vec![Self::new_empty(field.data_type())]
            }
            DataType::FixedSizeList(field, _) => {
                vec![Self::new_empty(field.data_type())]
            }
            DataType::LargeList(field) => {
                vec![Self::new_empty(field.data_type())]
            }
            DataType::Struct(fields) => fields
                .iter()
                .map(|field| Self::new_empty(field.data_type()))
                .collect(),
            DataType::Map(field, _) => {
                vec![Self::new_empty(field.data_type())]
            }
            DataType::Union(_) => unimplemented!(),
            DataType::Dictionary(_, data_type) => {
                vec![Self::new_empty(data_type)]
            }
            DataType::Float16 => unreachable!(),
        };

        // Data was constructed correctly above
        unsafe {
            Self::new_unchecked(
                data_type.clone(),
                0,
                Some(0),
                None,
                0,
                buffers,
                child_data,
            )
        }
    }
