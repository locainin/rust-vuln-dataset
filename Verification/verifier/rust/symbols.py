# Relate public function paths to parsed declarations

import re

from .parser import rust_nodes
from .tokens import tokenize


def target(pair: str, functions: tuple[str, ...]) -> tuple[str, ...] | None:
    matches: list[tuple[tuple[str, ...], str]] = []
    for function in functions:
        segments = function.split("::")
        # A matching slug identifies whether the first segment is a package
        for path in (segments, segments[1:]):
            name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", "_".join(path))
            name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name).lower()
            candidate = tuple(path)
            if name == pair and (candidate, function) not in matches:
                matches.append((candidate, function))
    matched_functions = {function for _, function in matches}
    return matches[0][0] if len(matched_functions) == 1 else None


def path(blob: bytes, node: dict) -> tuple[str, ...] | None:
    name = node.get("metaVariables", {}).get("single", {}).get("NAME")
    if name is None:
        return None
    bounds = node["range"]["byteOffset"]
    nodes = rust_nodes(blob)
    parents = [
        parent
        for parent in nodes
        if parent["ruleId"] in {"item", "module"}
        and parent["range"]["byteOffset"]["start"] < bounds["start"]
        and bounds["end"] < parent["range"]["byteOffset"]["end"]
    ]
    parents.sort(key=lambda parent: parent["range"]["byteOffset"]["start"])
    nearest = parents[-1] if parents else None
    modules = [
        parent["metaVariables"]["single"]["NAME"]["text"]
        for parent in parents
        if parent["ruleId"] == "module"
    ]

    # A top-level or module function has no receiver type to inspect
    if nearest is None or nearest["ruleId"] == "module":
        return (*modules, name["text"])

    # Nested functions are not associated with the outer declaration
    nearest_header = nearest["text"].split("{", 1)[0]
    if re.search(r"\bfn\s+(?:r#)?[A-Za-z_]\w*", nearest_header):
        return None

    # Trait methods use the trait name as their published path component
    trait = re.search(r"\btrait\s+(?:r#)?([A-Za-z_]\w*)", nearest_header)
    if trait is not None:
        return (*modules, trait[1], name["text"])

    # The nearest declaration must itself be an inherent impl
    owner = next(
        (
            parent
            for parent in nodes
            if parent["ruleId"] == "owner" and parent["range"] == nearest["range"]
        ),
        None,
    )
    if owner is None:
        return None

    # The grammar supplies the receiver type; generic arguments do not name it
    receiver = owner["metaVariables"]["single"]["TYPE"]["text"]
    parts, depth, closed = [], 0, False
    for token in tokenize(receiver):
        # Generic arguments may nest, but a path after them names another type
        if closed:
            return None
        if token.text == "<":
            depth += 1
        elif token.text == ">":
            depth -= 1
            closed = depth == 0
        elif depth == 0:
            parts.append(token.text)
    receiver = "".join(parts)
    if depth or not re.fullmatch(r"[A-Za-z_]\w*(?:::[A-Za-z_]\w*)*", receiver):
        return None
    return (*modules, *receiver.split("::"), name["text"])
