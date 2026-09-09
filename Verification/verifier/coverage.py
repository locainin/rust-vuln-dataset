# Account for every source case through curation or an explicit exclusion


def coverage(source: set[str], curated: set[str], excluded: set[str]) -> list[str]:
    errors = []
    if not curated:
        errors.append("no curated cases")
    for identifiers, label in (
        (curated & excluded, "both curated and excluded"),
        (source - curated - excluded, "unaccounted seed cases"),
        ((curated | excluded) - source, "unknown seed cases"),
    ):
        if identifiers:
            errors.append(f"{label}: {', '.join(sorted(identifiers))}")
    return errors
