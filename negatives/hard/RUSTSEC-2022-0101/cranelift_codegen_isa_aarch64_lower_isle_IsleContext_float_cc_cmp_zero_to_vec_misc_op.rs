    fn float_cc_cmp_zero_to_vec_misc_op(&mut self, cond: &FloatCC) -> VecMisc2 {
        match cond {
            &FloatCC::Equal => VecMisc2::Fcmeq0,
            &FloatCC::GreaterThanOrEqual => VecMisc2::Fcmge0,
            &FloatCC::LessThanOrEqual => VecMisc2::Fcmle0,
            &FloatCC::GreaterThan => VecMisc2::Fcmgt0,
            &FloatCC::LessThan => VecMisc2::Fcmlt0,
            _ => panic!(),
        }
    }
