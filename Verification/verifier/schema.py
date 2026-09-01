# Canonical RustXec metadata fields in required YAML order
EXPECTED_FIELDS = [
    "id",
    "package",
    "date",
    "categories",
    "CWE",
    "url",
    "references",
    "severity",
    "aliases",
    "keywords",
    "versions",
    "affected",
    "affected.functions",
    "fix commit links",
    "pov candidate links",
]

# The audited RustXec source snapshot has exactly this many rows
SOURCE_ROW_COUNT = 102

# Empty CSV values may be completed only in these authoritative metadata fields
ENRICHABLE_FIELDS = frozenset(
    {
        "categories",
        "CWE",
        "references",
        "severity",
        "aliases",
        "url",
        "fix commit links",
        "pov candidate links",
    }
)

# Link fields allow additional verified URLs when every CSV URL is preserved
LINK_FIELDS = frozenset(
    {
        "url",
        "references",
        "fix commit links",
        "pov candidate links",
    }
)
