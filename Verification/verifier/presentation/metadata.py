# Render metadata findings without repeating validation

import pprint
from typing import Any, TextIO

from ..metadata.inspection import Metadata
from ..metadata.schema import EXPECTED_FIELDS
from .console import Colorizer
from .report import check


def _display(value: Any) -> str:
    # Failure values use stable formatting without hiding null
    if value is None:
        return "null"
    return pprint.pformat(value, sort_dicts=True, width=110)


def _found_display(value: Any) -> str:
    # Found values stay compact enough for one report line
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def metadata_report(
    result: Metadata,
    stream: TextIO,
    colors: Colorizer,
) -> None:
    errors, found, failures = result.errors, result.found, result.failures

    # File failures have no fields to render
    if errors == ["metadata.yaml is missing"]:
        check("metadata.yaml", "FAIL", "missing", stream, colors)
        return
    if len(errors) == 1 and errors[0].startswith("metadata.yaml:"):
        check("metadata.yaml", "FAIL", errors[0].split(": ", 1)[1], stream, colors)
        return

    if errors:
        check(
            "Metadata",
            "FAIL",
            f"{len(errors)} issue(s)",
            stream,
            colors,
        )

        # Comparison failures include values while identity failures stay concise
        failures_by_message = {
            f"{issue['field']}: {issue['reason']}": issue for issue in failures
        }
        for error in errors:
            matching = failures_by_message.get(error)
            if matching is None:
                check("metadata", "FAIL", error, stream, colors, indent="    ")
                continue

            check(
                matching["field"],
                "FAIL",
                "",
                stream,
                colors,
                indent="    ",
            )
            print(f"      CSV:  {_display(matching['csv'])}", file=stream)
            print(f"      YAML: {_display(matching['yaml'])}", file=stream)
    else:
        check(
            "Metadata",
            "OK",
            f"{len(EXPECTED_FIELDS)} fields",
            stream,
            colors,
        )

    # Found enrichment is visible but never counted as a failure
    for issue in found:
        check(
            issue["field"],
            "FOUND",
            _found_display(issue["found"]),
            stream,
            colors,
            indent="    ",
        )
