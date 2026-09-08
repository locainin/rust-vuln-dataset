    pub fn new<V, S>(variable: V, subscripts: &[S]) -> Key
    where
        V: Into<String>,
        S: Into<Vec<u8>> + Clone,
    {
        Key {
            variable: variable.into(),
            // NOTE: we cannot remove this copy because `node_next_st` mutates subscripts
            // and `node_subscript_st` mutates the variable
            subscripts: subscripts.iter().cloned().map(|slice| slice.into()).collect(),
        }
    }
