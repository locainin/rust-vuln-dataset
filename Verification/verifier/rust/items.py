# Identify complete local Rust items for pair deletion checks

import re

from .parser import item_at, rust_nodes
from .tokens import render, tokenize


def _template_tokens(tokens, left, right):
    # A snippet must contain whole sibling tokens, never part of a literal or comment
    selected = [token for token in tokens if left <= token.start < token.end <= right]
    if selected:
        position = tokens.index(selected[0])
        return not (
            position >= 2
            and tokens[position - 2].text == "#"
            and tokens[position - 1].text == "["
        )
    for token in tokens:
        if token.kind == "group" and token.start < left and right <= token.end:
            return _template_tokens(token.children, left, right)
    return False


def curated_node(blob: bytes, left: int, right: int) -> dict | None:
    # Return a complete item, including supported quoted macro templates
    # Ordinary syntax is authoritative before the narrow quote-template fallback
    node = item_at(blob, left, right, allow_macros=True)
    if node is not None:
        return node
    snippet = blob[left:right]
    for wrapper in rust_nodes(blob):
        # Only macro wrappers can contain Rust-like quoted declarations
        bounds = wrapper["range"]["byteOffset"]
        if wrapper["ruleId"] not in {"macro", "macro_definition"}:
            continue
        if not bounds["start"] < left < right < bounds["end"]:
            continue
        text = blob[bounds["start"] : bounds["end"]].decode("utf-8")
        char_left = len(blob[bounds["start"] : left].decode("utf-8"))
        char_right = len(blob[bounds["start"] : right].decode("utf-8"))
        if not _template_tokens(tokenize(text), char_left, char_right):
            continue
        # Quote interpolation is not Rust syntax; mask only parser-reported markers
        parsed = bytearray(snippet)
        for error in rust_nodes(snippet):
            if error["ruleId"] != "parse_error":
                continue
            offset = error["range"]["byteOffset"]
            if not text.lstrip().startswith("quote!") or error["text"] != "#":
                return None
            if not re.match(rb"[A-Za-z_]\w*", snippet[offset["end"] :]):
                return None
            parsed[offset["start"] : offset["end"]] = b" "
        node = item_at(bytes(parsed), 0, len(parsed), allow_macros=True)
        if node is not None:
            return {**node, "template": True}
    return None


def _impl_identity(header: str) -> str:
    # Generic parameter names are normalized so formatting changes do not alter identity
    tokens = list(tokenize(header))
    if tokens and tokens[0].text == "unsafe":
        tokens.pop(0)
    if not tokens or tokens.pop(0).text != "impl":
        raise ValueError("unrecognized impl declaration")
    parameters = {}
    if tokens and tokens[0].text == "<":
        # Replace each top-level generic declaration with a stable ordinal
        depth, segment = 1, []
        tokens.pop(0)
        while tokens and depth:
            token = tokens.pop(0)
            if token.text == "<":
                depth += 1
            elif token.text == ">":
                depth -= 1
            if depth == 0 or (depth == 1 and token.text == ","):
                names = [part.text for part in segment if part.text != "const"]
                if names:
                    parameters[names[0]] = f"parameter_{len(parameters)}"
                segment = []
            else:
                segment.append(token)
        if depth:
            raise ValueError("unbalanced impl parameters")
    for position, token in enumerate(tokens):
        if token.text == "where":
            tokens = tokens[:position]
            break
    rendered = render(tokens)
    return re.sub(
        r"'?[A-Za-z_]\w*", lambda match: parameters.get(match[0], match[0]), rendered
    )


def _declaration(node: dict) -> tuple[str, str]:
    header = node["text"].split("{", 1)[0]
    if re.match(r"\s*(?:unsafe\s+)?impl\b", header):
        return "impl", _impl_identity(header)
    match = re.search(
        r"\b(fn|struct|enum|trait|mod|macro_rules!)\s+((?:r#)?[A-Za-z_]\w*)", header
    )
    if match is None:
        raise ValueError("parsed declaration identity cannot be established")
    return match[1], match[2]


def _identity(blob: bytes, node: dict) -> tuple:
    # Parent declarations distinguish same-named methods in separate impl blocks
    bounds = node["range"]["byteOffset"]
    parents = [
        parent
        for parent in rust_nodes(blob)
        if parent["ruleId"] in {"item", "module"}
        and parent["range"]["byteOffset"]["start"] < bounds["start"]
        and bounds["end"] < parent["range"]["byteOffset"]["end"]
    ]
    parents.sort(key=lambda parent: parent["range"]["byteOffset"]["start"])
    return tuple(_declaration(parent) for parent in [*parents, node])


def item_removed(before: bytes, after: bytes, snippet: bytes, offset: int) -> bool:
    # Check that a complete item disappeared without confusing same-name items
    # Reuse the exact byte location already established by snippet matching
    original = curated_node(before, offset, offset + len(snippet))
    if original is None or original.get("template"):
        raise ValueError("deleted-item declaration identity cannot be established")
    identity = _identity(before, original)
    # Invalid replacement syntax cannot prove that an item was removed
    nodes = rust_nodes(after) if after else []
    if any(node["ruleId"] == "parse_error" for node in nodes):
        raise ValueError(
            "deleted-item absence cannot be established in invalid Rust source"
        )
    for node in nodes:
        if (
            node["ruleId"] in {"item", "macro_definition"}
            and _identity(after, node) == identity
        ):
            return False
        if node["ruleId"] in {"macro", "macro_definition"}:
            # Opaque macro output cannot prove that a same-named item disappeared
            kind, name = identity[-1]
            if kind == "fn" and re.search(rf"\bfn\s+{re.escape(name)}\b", node["text"]):
                raise ValueError("deleted-item absence is ambiguous in macro output")
    return True
