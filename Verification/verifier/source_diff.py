from __future__ import annotations

import difflib
import textwrap


def unified_source_diff(vulnerable: str, fixed: str) -> list[str]:
    # Dedent copies for display while exact verification keeps original bytes
    display_vulnerable = textwrap.dedent(vulnerable)
    display_fixed = textwrap.dedent(fixed)

    # Direction matters because removals are vulnerable and additions are repaired
    return list(
        difflib.unified_diff(
            display_vulnerable.splitlines(),
            display_fixed.splitlines(),
            fromfile="vulnerable",
            tofile="fixed",
            n=2,
            lineterm="",
        )
    )
