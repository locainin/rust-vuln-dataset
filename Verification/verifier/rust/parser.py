# Parse local Rust source and identify complete item boundaries

from __future__ import annotations

import json
import subprocess
from functools import lru_cache

RUST_PARSE_TIMEOUT = 45


@lru_cache(maxsize=128)
def rust_nodes(blob: bytes) -> list[dict]:
    # Return syntax nodes reported by the installed Rust grammar
    # Rules stay local to this call so the parser has no repository assumptions
    rules = [
        {
            "id": "item",
            "language": "Rust",
            "rule": {
                "any": [
                    {
                        "kind": "function_item",
                        "has": {"field": "name", "pattern": "$NAME"},
                    },
                    *[
                        {"kind": kind}
                        for kind in (
                            "impl_item",
                            "struct_item",
                            "enum_item",
                            "trait_item",
                        )
                    ],
                ]
            },
        },
        {"id": "attribute", "language": "Rust", "rule": {"kind": "attribute_item"}},
        {
            "id": "module",
            "language": "Rust",
            "rule": {"kind": "mod_item", "has": {"field": "name", "pattern": "$NAME"}},
        },
        {
            "id": "owner",
            "language": "Rust",
            "rule": {
                "kind": "impl_item",
                "has": {"field": "type", "pattern": "$TYPE"},
                "not": {"has": {"field": "trait", "regex": ".*"}},
            },
        },
        {"id": "macro", "language": "Rust", "rule": {"kind": "macro_invocation"}},
        {
            "id": "macro_definition",
            "language": "Rust",
            "rule": {"kind": "macro_definition"},
        },
        {
            "id": "comment",
            "language": "Rust",
            "rule": {"any": [{"kind": "line_comment"}, {"kind": "block_comment"}]},
        },
        {"id": "parse_error", "language": "Rust", "rule": {"kind": "ERROR"}},
    ]
    command = [
        "ast-grep",
        "scan",
        "--inline-rules",
        "\n---\n".join(json.dumps(rule) for rule in rules),
        "--stdin",
        "--json=compact",
    ]
    # Stdin avoids temporary files and preserves the exact bytes under review
    try:
        result = subprocess.run(
            command,
            input=blob,
            capture_output=True,
            check=False,
            timeout=RUST_PARSE_TIMEOUT,
        )
    except subprocess.TimeoutExpired as error:
        raise ValueError(
            "ast-grep Rust parser timed out after "
            f"{RUST_PARSE_TIMEOUT} seconds while parsing {len(blob)} bytes"
        ) from error
    if result.returncode not in {0, 1}:
        raise ValueError(
            f"Rust parser failed: {result.stderr.decode(errors='replace').strip()}"
        )
    # ast-grep uses status one when a valid scan has no matches
    return json.loads(result.stdout)


def _only_spacing(blob: bytes, left: int, right: int) -> bool:
    comments = sorted(
        (node["range"]["byteOffset"]["start"], node["range"]["byteOffset"]["end"])
        for node in rust_nodes(blob)
        if node["ruleId"] == "comment"
    )
    # Comments between an attribute and its item do not detach the attribute
    for comment_start, comment_end in comments:
        if left <= comment_start < comment_end <= right:
            if blob[left:comment_start].strip():
                return False
            left = comment_end
    return not blob[left:right].strip()


def item_at(
    blob: bytes, first: int, last: int, *, allow_macros: bool = False
) -> dict | None:
    # Return the complete item occupying an exact byte range
    # A match must fit wholly inside the requested bytes
    if not 0 <= first < last <= len(blob):
        raise ValueError("item byte range is outside the local source")
    nodes = rust_nodes(blob)
    kinds = {"item", "macro_definition"} if allow_macros else {"item"}

    attributes = []
    # Parse errors inside a candidate invalidate the extraction
    for node in nodes:
        offset = node["range"]["byteOffset"]
        left, right = offset["start"], offset["end"]
        if node["ruleId"] == "parse_error" and left < last and right > first:
            return None
        if node["ruleId"] == "attribute" and first <= left < right <= last:
            attributes.append((left, right))
    for node in nodes:
        left = node["range"]["byteOffset"]["start"]
        right = node["range"]["byteOffset"]["end"]
        if node["ruleId"] not in kinds or not first <= left < right <= last:
            continue
        if not _only_spacing(blob, right, last):
            continue
        cursor = first
        for attr_start, attr_end in sorted(attributes):
            if attr_end <= left:
                if not _only_spacing(blob, cursor, attr_start):
                    break
                cursor = attr_end
        if _only_spacing(blob, cursor, left):
            # An immediately attached attribute must not be lost at extraction
            preceding = [
                n
                for n in nodes
                if n["ruleId"] == "attribute"
                and n["range"]["byteOffset"]["end"] <= first
            ]
            if any(
                _only_spacing(blob, n["range"]["byteOffset"]["end"], first)
                for n in preceding
            ):
                return None
            return node
    return None
