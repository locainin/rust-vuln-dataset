    fn clean_dom(&self, mut dom: RcDom) -> Document {
        let mut stack = Vec::new();
        let mut removed = Vec::new();
        let link_rel = self
            .link_rel
            .map(|link_rel| format_tendril!("{}", link_rel));
        if link_rel.is_some() {
            assert!(self.generic_attributes.get("rel").is_none());
            assert!(self
                .tag_attributes
                .get("a")
                .and_then(|a| a.get("rel"))
                .is_none());
        }
        assert!(self.allowed_classes.is_empty() || !self.generic_attributes.contains("class"));
        for (tag_name, _classes) in &self.allowed_classes {
            assert!(self
                .tag_attributes
                .get(tag_name)
                .and_then(|a| a.get("class"))
                .is_none());
        }
        for tag_name in &self.clean_content_tags {
            assert!(!self.tags.contains(tag_name));
            assert!(!self.tag_attributes.contains_key(tag_name));
        }
        let url_base = if let UrlRelative::RewriteWithBase(ref base) = self.url_relative {
            Some(base)
        } else {
            None
        };
        let body = {
            let children = dom.document.children.borrow();
            children[0].clone()
        };
        stack.extend(
            replace(&mut *body.children.borrow_mut(), Vec::new())
                .into_iter()
                .rev(),
        );
        // This design approach is used to prevent pathological content from producing
        // a stack overflow. The `stack` contains to-be-cleaned nodes, while `remove`,
        // of course, contains nodes that need to be dropped (we can't just drop them,
        // because they could have a very deep child tree).
        while let Some(mut node) = stack.pop() {
            let parent = node.parent
                .replace(None).expect("a node in the DOM will have a parent, except the root, which is not processed")
                .upgrade().expect("a node's parent will be pointed to by its parent (or the root pointer), and will not be dropped");
            if self.clean_node_content(&node) {
                removed.push(node);
                continue;
            }
            let pass = self.clean_child(&mut node, url_base);
            if pass {
                self.adjust_node_attributes(&mut node, &link_rel, url_base, self.id_prefix);
                dom.append(&parent.clone(), NodeOrText::AppendNode(node.clone()));
            } else {
                for sub in node.children.borrow_mut().iter_mut() {
                    sub.parent.replace(Some(Rc::downgrade(&parent)));
                }
            }
            stack.extend(
                replace(&mut *node.children.borrow_mut(), Vec::new())
                    .into_iter()
                    .rev(),
            );
            if !pass {
                removed.push(node);
            }
        }
        // Now, imperatively clean up all of the child nodes.
        // Otherwise, we could wind up with a DoS, either caused by a memory leak,
        // or caused by a stack overflow.
        while let Some(node) = removed.pop() {
            removed.extend_from_slice(&replace(&mut *node.children.borrow_mut(), Vec::new())[..]);
        }
        Document(dom)
    }
