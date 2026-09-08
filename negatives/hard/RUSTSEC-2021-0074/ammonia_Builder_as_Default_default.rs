    fn default() -> Self {
        #[cfg_attr(rustfmt, rustfmt_skip)]
        let tags = hashset![
            "a", "abbr", "acronym", "area", "article", "aside", "b", "bdi",
            "bdo", "blockquote", "br", "caption", "center", "cite", "code",
            "col", "colgroup", "data", "dd", "del", "details", "dfn", "div",
            "dl", "dt", "em", "figcaption", "figure", "footer", "h1", "h2",
            "h3", "h4", "h5", "h6", "header", "hgroup", "hr", "i", "img",
            "ins", "kbd", "kbd", "li", "map", "mark", "nav", "ol", "p", "pre",
            "q", "rp", "rt", "rtc", "ruby", "s", "samp", "small", "span",
            "strike", "strong", "sub", "summary", "sup", "table", "tbody",
            "td", "th", "thead", "time", "tr", "tt", "u", "ul", "var", "wbr"
        ];
        let clean_content_tags = hashset!["script", "style"];
        let generic_attributes = hashset!["lang", "title"];
        let tag_attributes = hashmap![
            "a" => hashset![
                "href", "hreflang"
            ],
            "bdo" => hashset![
                "dir"
            ],
            "blockquote" => hashset![
                "cite"
            ],
            "col" => hashset![
                "align", "char", "charoff", "span"
            ],
            "colgroup" => hashset![
                "align", "char", "charoff", "span"
            ],
            "del" => hashset![
                "cite", "datetime"
            ],
            "hr" => hashset![
                "align", "size", "width"
            ],
            "img" => hashset![
                "align", "alt", "height", "src", "width"
            ],
            "ins" => hashset![
                "cite", "datetime"
            ],
            "ol" => hashset![
                "start"
            ],
            "q" => hashset![
                "cite"
            ],
            "table" => hashset![
                "align", "char", "charoff", "summary"
            ],
            "tbody" => hashset![
                "align", "char", "charoff"
            ],
            "td" => hashset![
                "align", "char", "charoff", "colspan", "headers", "rowspan"
            ],
            "tfoot" => hashset![
                "align", "char", "charoff"
            ],
            "th" => hashset![
                "align", "char", "charoff", "colspan", "headers", "rowspan", "scope"
            ],
            "thead" => hashset![
                "align", "char", "charoff"
            ],
            "tr" => hashset![
                "align", "char", "charoff"
            ],
        ];
        let tag_attribute_values = hashmap![];
        let set_tag_attribute_values = hashmap![];
        let url_schemes = hashset![
            "bitcoin",
            "ftp",
            "ftps",
            "geo",
            "http",
            "https",
            "im",
            "irc",
            "ircs",
            "magnet",
            "mailto",
            "mms",
            "mx",
            "news",
            "nntp",
            "openpgp4fpr",
            "sip",
            "sms",
            "smsto",
            "ssh",
            "tel",
            "url",
            "webcal",
            "wtai",
            "xmpp"
        ];
        let allowed_classes = hashmap![];

        Builder {
            tags,
            clean_content_tags,
            tag_attributes,
            tag_attribute_values,
            set_tag_attribute_values,
            generic_attributes,
            url_schemes,
            url_relative: UrlRelative::PassThrough,
            attribute_filter: None,
            link_rel: Some("noopener noreferrer"),
            allowed_classes,
            strip_comments: true,
            id_prefix: None,
            generic_attribute_prefixes: None,
        }
    }
