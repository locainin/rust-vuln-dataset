    pub fn remove(&mut self, index: usize) -> T where T: Clone {
        assert!(index < self.len(),"remove out of bounds");
        if let Some(e) = Arc::get_mut(&mut self.inner) {
            e.truncate(self.slice.end);
            self.slice.end -= 1;
            e.remove(self.slice.start + index)
        }else{
            let origin = &self[..];
            let mut dest = Vec::with_capacity(self.len()-1);
            let left = &origin[..index];
            dest.extend_from_slice(left);
            let removed = origin[index].clone();
            let right = &origin[(index+1)..];
            dest.extend_from_slice(right);
            *self = Self::from(dest);
            removed
        }
    }
