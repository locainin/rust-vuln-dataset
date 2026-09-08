fn territory<R: BufRead>(
    reader: &mut Reader<R>,
    e: &events::BytesStart<'_>,
) -> Result<Metadata, error::LoadMetadata> {
    let mut buffer = Vec::new();
    let mut meta = Metadata::default();

    for attr in e.attributes() {
        let Attribute { key, value } = attr.map_err(quick_xml::Error::InvalidAttr)?;

        match (str::from_utf8(key.into_inner())?, str::from_utf8(&value)?) {
            ("id", value) => meta.id = Some(value.into()),

            ("countryCode", value) => meta.country_code = Some(value.parse()?),

            ("internationalPrefix", value) => meta.international_prefix = Some(value.into()),

            ("preferredInternationalPrefix", value) => {
                meta.preferred_international_prefix = Some(value.into())
            }

            ("nationalPrefix", value) => meta.national_prefix = Some(value.into()),

            ("preferredExtnPrefix", value) => meta.preferred_extension_prefix = Some(value.into()),

            ("nationalPrefixForParsing", value) => {
                meta.national_prefix_for_parsing = Some(value.into())
            }

            ("nationalPrefixTransformRule", value) => {
                meta.national_prefix_transform_rule = Some(value.into())
            }

            ("mainCountryForCode", value) => meta.main_country_for_code = value.parse()?,

            ("leadingDigits", value) => meta.leading_digits = Some(value.into()),

            ("mobileNumberPortableRegion", value) => meta.mobile_number_portable = value.parse()?,

            ("nationalPrefixFormattingRule", value) => {
                meta.defaults.format.national_prefix_formatting_rule = Some(value.into())
            }

            ("nationalPrefixOptionalWhenFormatting", value) => {
                meta.defaults
                    .format
                    .national_prefix_optional_when_formatting = value.parse()?
            }

            ("carrierCodeFormattingRule", value) => {
                meta.defaults.format.domestic_carrier = Some(value.into())
            }

            (name, value) => {
                return Err(error::Metadata::UnhandledAttribute {
                    phase: "format".into(),
                    name: name.into(),
                    value: value.into(),
                }
                .into())
            }
        }
    }

    loop {
        match reader.read_event_into(&mut buffer)? {
            Event::Text(_) | Event::Comment(_) => (),

            Event::Start(ref e) => match e.name().into_inner() {
                name @ b"references" | name @ b"areaCodeOptional" => ignore(reader, name)?,

                name @ b"generalDesc" => meta.general = Some(descriptor(reader, &meta, name)?),

                name @ b"fixedLine" => meta.fixed_line = Some(descriptor(reader, &meta, name)?),

                name @ b"mobile" => meta.mobile = Some(descriptor(reader, &meta, name)?),

                name @ b"tollFree" => meta.toll_free = Some(descriptor(reader, &meta, name)?),

                name @ b"premiumRate" => meta.premium_rate = Some(descriptor(reader, &meta, name)?),

                name @ b"sharedCost" => meta.shared_cost = Some(descriptor(reader, &meta, name)?),

                name @ b"personalNumber" => {
                    meta.personal_number = Some(descriptor(reader, &meta, name)?)
                }

                name @ b"voip" => meta.voip = Some(descriptor(reader, &meta, name)?),

                name @ b"pager" => meta.pager = Some(descriptor(reader, &meta, name)?),

                name @ b"uan" => meta.uan = Some(descriptor(reader, &meta, name)?),

                name @ b"emergency" => meta.emergency = Some(descriptor(reader, &meta, name)?),

                name @ b"voicemail" => meta.voicemail = Some(descriptor(reader, &meta, name)?),

                name @ b"noInternationalDialling" => {
                    meta.no_international = Some(descriptor(reader, &meta, name)?)
                }

                name @ b"availableFormats" => {
                    let (national, international) = formats(reader, &meta, name)?;

                    meta.formats = national;
                    meta.international_formats = international;
                }

                name => {
                    return Err(error::Metadata::UnhandledElement {
                        phase: "territory".into(),
                        name: str::from_utf8(name)?.into(),
                    }
                    .into())
                }
            },

            Event::End(ref e) if e.name().into_inner() == b"territory" => return Ok(meta),

            Event::End(ref e) => {
                return Err(error::Metadata::MismatchedTag(
                    str::from_utf8(e.name().into_inner())?.into(),
                )
                .into())
            }

            Event::Eof => return Err(error::Metadata::UnexpectedEof.into()),

            event => {
                return Err(error::Metadata::UnhandledEvent {
                    phase: "territory".into(),
                    event: format!("{:?}", event),
                }
                .into())
            }
        }
    }
}
