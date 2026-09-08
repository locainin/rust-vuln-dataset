    pub fn new(memory: M) -> Self {
        let page_size = match (K::BOUND, V::BOUND) {
            // The keys and values are both bounded.
            (
                StorableBound::Bounded {
                    max_size: max_key_size,
                    ..
                },
                StorableBound::Bounded {
                    max_size: max_value_size,
                    ..
                },
            ) => {
                // Get the maximum possible node size.
                let max_node_size = Node::<K>::max_size(max_key_size, max_value_size).get();

                // A node can have at most 11 entries, and an analysis has shown that ~70% of all
                // nodes have <= 8 entries. We can therefore use a page size that's 8/11 the
                // maximum size with little performance difference but with a significant storage
                // saving. We round the 8/11 to be 3/4.
                PageSize::Value((max_node_size * 3 / 4) as u32)
            }
            // Use a default page size.
            _ => PageSize::Value(DEFAULT_PAGE_SIZE),
        };

        let btree = Self {
            root_addr: NULL,
            allocator: Allocator::new(
                memory,
                Address::from(ALLOCATOR_OFFSET as u64),
                page_size.get().into(),
            ),
            version: Version::V2(page_size),
            length: 0,
            _phantom: PhantomData,
        };

        btree.save();
        btree
    }
