    fn extend<I: iter::IntoIterator<Item=A::Item>>(&mut self, iterable: I) {
        let mut iter = iterable.into_iter();
        let (lower_bound, upper_bound) = iter.size_hint();
        let upper_bound = upper_bound.expect("iterable must provide upper bound.");
        assert!(self.len() + upper_bound <= self.capacity());

        unsafe {
            let len = self.len();
            let ptr = self.as_mut_ptr().padd(len);
            let mut count = 0;
            while count < lower_bound {
                if let Some(out) = iter.next() {
                    ptr::write(ptr.padd(count), out);
                    count += 1;
                } else {
                    break;
                }
            }
            self.set_len(len + count);
        }

        for elem in iter {
            self.push(elem);
        }
    }
