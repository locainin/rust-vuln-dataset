# Match snippets to complete items using published declaration context

import subprocess

from ..rust.items import curated_node
from ..rust import symbols


def match(
    container: bytes,
    snippet: bytes,
    relative_path: str,
    container_name: str,
    errors: list[str],
    target: tuple[str, ...] | None = None,
) -> tuple[tuple[int, int] | None, int, int | None]:
    count = container.count(snippet)
    if count == 0:
        errors.append(f"{relative_path} is not an exact substring of {container_name}")
        return None, 0, None
    if count > 1 and target is None:
        errors.append(f"{relative_path} has ambiguous matches in {container_name}")
        return None, count, None

    try:
        offsets = []
        offset = container.find(snippet)
        while offset != -1:
            node = curated_node(container, offset, offset + len(snippet))
            if node is None:
                if count == 1:
                    errors.append(
                        f"{relative_path} is not a complete Rust item "
                        "with attached attributes"
                    )
                    return None, count, None
            elif target is not None:
                path = symbols.path(container, node)
                # Snapshot files may omit outer modules, but visible parents must agree
                if path and target[-len(path) :] == path:
                    offsets.append(offset)
            else:
                offsets.append(offset)
            offset = container.find(snippet, offset + len(snippet))
        if len(offsets) != 1:
            if target is not None and count == 1:
                errors.append(
                    f"{relative_path} does not match the published function context"
                )
                return None, count, None
            errors.append(f"{relative_path} has ambiguous matches in {container_name}")
            return None, count, None
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        errors.append(f"{relative_path}: {error}")
        return None, count, None

    first = container.count(b"\n", 0, offsets[0]) + 1
    lines = snippet.count(b"\n") + (not snippet.endswith(b"\n"))
    return (first, first + lines - 1), count, offsets[0]
