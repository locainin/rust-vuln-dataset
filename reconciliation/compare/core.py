import csv
import hashlib
import io
import itertools
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from compare.repository import (
    HALURUST_REVISION,
    read_local_bytes,
    require_tracked_file,
    tracked_files,
    verify_checkout,
)


IDENTIFIER_PATTERN = re.compile(
    r"\b(?:"
    r"CVE-\d{4}-\d+"
    r"|RUSTSEC-\d{4}-\d+"
    r"|GHSA-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}"
    r")\b",
    re.IGNORECASE,
)


REVISION_PATTERN = re.compile(
    r"/(?:commit|tree|blob)/"
    r"([0-9a-f]{40})(?=[^0-9a-f]|$)"
)


DATASET_ORDER = {"RustXec": 0, "HaluRust": 1, "RustMizan": 2}


ADVISORY_FIELDS = {"CVE", "RUSTSEC", "GHSA"}


COMMIT_FIELDS = {
    "Repair commit",
    "Vulnerable revision",
    "Fixed revision",
}


def extract_identifiers(value):
    identifiers = set()
    for identifier in IDENTIFIER_PATTERN.findall(str(value)):
        if identifier.lower().startswith("ghsa-"):
            identifiers.add("GHSA-" + identifier[5:].lower())
        else:
            identifiers.add(identifier.upper())
    return identifiers


def extract_commit_revisions(value):
    return set(REVISION_PATTERN.findall(str(value)))


def add_fact(index, family, native_id, field, value, source):
    category = "Commit" if field in COMMIT_FIELDS else field
    index[category, value].add((family, native_id, field, source))


def add_identifiers(index, family, native_id, value, source):
    for identifier in extract_identifiers(value):
        field = identifier.split("-", 1)[0]
        add_fact(index, family, native_id, field, identifier, source)


def add_commit_revisions(index, family, native_id, value, field, source):
    for revision in extract_commit_revisions(value):
        add_fact(index, family, native_id, field, revision, source)


def add_source_hash(index, family, native_id, data, source):
    # Empty deletion results carry no source identity information
    if data:
        digest = hashlib.sha256(data).hexdigest()
        add_fact(index, family, native_id, "Source SHA-256", digest, source)


def add_metadata(index, family, native_id, data, source):
    values = [data.get("id"), data.get("aliases"), data.get("url")]
    add_identifiers(index, family, native_id, values, source)
    add_commit_revisions(
        index, family, native_id, data.get("fix commit links"),
        "Repair commit", source,
    )


def collect_rustxec(root, local_files, index, counts, differences, retained):
    pair_sources = defaultdict(list)
    for relative in sorted(local_files):
        parts = relative.parts
        if (len(parts) == 5 and parts[0] == "manual" and parts[2] == "pairs"
                and parts[4] in {"vulnerable.rs", "fixed.rs"}):
            pair_sources[parts[1]].append(relative)
    # Preserve CSV claims in the differences table; prefer existing curated metadata
    source_csv = read_local_bytes(root, "Verification/source/metadata.csv", local_files)
    with io.StringIO(source_csv.decode(), newline="") as stream:
        seeds = list(csv.DictReader(stream))
    if len({row["id"] for row in seeds}) != len(seeds):
        raise ValueError("Duplicate RustXec source IDs")
    for row in seeds:
        native_id = row["id"]
        path = root / "manual" / native_id / "metadata.yaml"
        present = path.relative_to(root) in local_files
        counts["RustXec", "retained" if present else "excluded"] += 1
        if present:
            retained.add(("RustXec", native_id))
            current = yaml.safe_load(
                read_local_bytes(root, path.relative_to(root), local_files).decode()
            )
            source = path.relative_to(root).as_posix()
            historical_ids = extract_identifiers(
                [row["id"], row["aliases"], row["url"]]
            )
            curated_ids = extract_identifiers(
                [current["id"], current.get("aliases"), current.get("url")]
            )
            if historical_ids != curated_ids:
                differences.append(
                    (
                        "RustXec", native_id, "Verification/source/metadata.csv",
                        ", ".join(sorted(historical_ids)), source,
                        ", ".join(sorted(curated_ids)),
                    )
                )
        else:
            current, source = row, "Verification/source/metadata.csv#" + native_id
        add_metadata(index, "RustXec", native_id, current, source)
        for filename in ("vulnerable.rs", "fixed.rs"):
            for relative in pair_sources[native_id]:
                if relative.name != filename:
                    continue
                add_source_hash(
                    index, "RustXec", native_id,
                    read_local_bytes(root, relative, local_files),
                    relative.as_posix(),
                )


def halurust_inventory(halu_source):
    upstream_files = tracked_files(halu_source)
    names = {}
    for state in ("Positive", "Negative"):
        names[state] = {
            path.name for path in upstream_files
            if path.parent == Path("Data") / state and path.suffix == ".rs"
        }
    if not names["Positive"] or names["Positive"] != names["Negative"]:
        raise ValueError("Tracked HaluRust Positive/Negative filename sets differ or are empty")
    return sorted(names["Positive"])


def collect_halurust(root, halu_source, local_files, index, counts, retained):
    case_ids = set()
    for path in local_files:
        if len(path.parts) >= 4 and path.parts[:2] == ("halurust", "cases"):
            case_ids.add(path.parts[2])

    source_case_ids = set()
    for filename in halurust_inventory(halu_source):
        native_id = Path(filename).stem
        # Upstream filenames include a CWE suffix; only the literal CVE is compared
        cve = native_id.split("_", 1)[0]
        if not re.fullmatch(r"CVE-\d{4}-\d+", cve) or cve in source_case_ids:
            raise ValueError(f"Unexpected or duplicate HaluRust filename identifier: {filename}")
        source_case_ids.add(cve)
        present = cve in case_ids
        counts["HaluRust", "retained" if present else "not retained"] += 1
        if present:
            retained.add(("HaluRust", native_id))
        relative_metadata = Path("halurust/cases") / cve / "metadata.yaml"
        if relative_metadata in local_files:
            add_metadata(
                index, "HaluRust", native_id,
                yaml.safe_load(read_local_bytes(root, relative_metadata, local_files).decode()),
                relative_metadata.as_posix(),
            )
        for state in ("Positive", "Negative"):
            relative = Path("Data") / state / filename
            source = f"HaluRust@{HALURUST_REVISION}:{relative}"
            add_identifiers(index, "HaluRust", native_id, cve, source)
            add_source_hash(
                index, "HaluRust", native_id, (halu_source / relative).read_bytes(), source,
            )
    if case_ids - source_case_ids:
        raise ValueError(f"Tracked HaluRust cases absent from upstream: {sorted(case_ids - source_case_ids)}")


def collect_rustmizan(
    mizan_source, mizan, local_mizan, lock, upstream_files,
    index, counts, differences, retained,
):
    rust_files = sorted(path for path in upstream_files if path.suffix == ".rs")
    # Native case IDs are the units; contexts and states are never separate cases
    upstream_ids = {case["id"] for case in mizan}
    included = set()
    for native_id, entry in lock["cases"].items():
        if entry["disposition"] == "included":
            included.add(native_id)
    retained_ids = {case["id"] for case in local_mizan}
    if upstream_ids != set(lock["cases"]) or included != retained_ids:
        raise ValueError("RustMizan source, source lock, and retained inventory disagree")
    for case in mizan:
        native_id = case["id"]
        disposition = lock["cases"][native_id]["disposition"]
        counts["RustMizan", "retained" if disposition == "included" else disposition] += 1
        if disposition == "included":
            retained.add(("RustMizan", native_id))
        prefix = f"RustMizan@{lock['upstream']['revision']}:"
        add_identifiers(
            index, "RustMizan", native_id, case["source_link"],
            prefix + "mizan.json#" + native_id,
        )
        readme = mizan_source / "samples" / native_id / "README.md"
        if readme.relative_to(mizan_source) in upstream_files:
            # Read explicit table fields only, not explanations or embedded code
            for line in readme.read_text().splitlines():
                cells = [cell.strip().strip("*").strip() for cell in line.split("|")]
                if len(cells) < 4:
                    continue
                label, value = cells[1:3]
                source = (
                    prefix + readme.relative_to(mizan_source).as_posix()
                    + ":" + label
                )
                if label in ADVISORY_FIELDS:
                    add_identifiers(index, "RustMizan", native_id, value, source)
                    table_ids = extract_identifiers(value)
                    if table_ids != extract_identifiers(case["source_link"]):
                        differences.append(
                            (
                                "RustMizan", native_id,
                                prefix + "mizan.json:source_link",
                                case["source_link"], source,
                                ", ".join(sorted(table_ids)),
                            )
                        )
                if label in {"Vulnerable Commit", "Fixed Commit"}:
                    if label == "Vulnerable Commit":
                        field = "Vulnerable revision"
                    else:
                        field = "Fixed revision"
                    add_commit_revisions(
                        index, "RustMizan", native_id, value, field, source,
                    )
        for sample in case["code_samples"]:
            project = Path("samples") / sample["path_to_crate"]
            require_tracked_file(mizan_source, project / "Cargo.toml", upstream_files)
            for relative in rust_files:
                if not relative.is_relative_to(project):
                    continue
                add_source_hash(
                    index, "RustMizan", native_id, (mizan_source / relative).read_bytes(),
                    prefix + relative.as_posix(),
                )


def find_intersections(index):
    # Keep each matching field separate, including commit fields with different roles
    matches = defaultdict(lambda: [set(), set()])
    for (_, value), entries in sorted(index.items()):
        ordered = sorted(
            entries, key=lambda entry: (DATASET_ORDER[entry[0]], *entry[1:])
        )
        for entry_a, entry_b in itertools.combinations(ordered, 2):
            family_a, native_id_a, field_a, source_a = entry_a
            family_b, native_id_b, field_b, source_b = entry_b
            if family_a == family_b:
                continue
            field = field_a if field_a == field_b else field_a + " / " + field_b
            sources = matches[
                family_a, native_id_a, family_b, native_id_b, field, value
            ]
            sources[0].add(source_a)
            sources[1].add(source_b)
    rows = []
    for key, (sources_a, sources_b) in sorted(matches.items()):
        rows.append(
            (
                *key,
                "; ".join(sorted(sources_a)),
                "; ".join(sorted(sources_b)),
            )
        )
    return rows


def compare_datasets(root, halu_source, mizan_source):
    local_files = tracked_files(root)
    lock = yaml.safe_load(
        read_local_bytes(root, "rustmizan/source-lock.yaml", local_files).decode()
    )
    verify_checkout(halu_source, HALURUST_REVISION)
    verify_checkout(mizan_source, lock["upstream"]["revision"])
    upstream_files = tracked_files(mizan_source)
    mizan_path = require_tracked_file(mizan_source, "mizan.json", upstream_files)
    mizan_bytes = mizan_path.read_bytes()
    if hashlib.sha256(mizan_bytes).hexdigest() != lock["upstream"]["metadata_sha256"]:
        raise ValueError("Pinned mizan.json does not match the existing source lock")
    mizan = json.loads(mizan_bytes)["vulnerabilities"]
    local_mizan = json.loads(
        read_local_bytes(root, "rustmizan/mizan.json", local_files).decode()
    )["vulnerabilities"]

    # The index exists only in memory and contains literal values with their origins
    index = defaultdict(set)
    counts = Counter()
    differences = []
    retained = set()

    collect_rustxec(root, local_files, index, counts, differences, retained)
    collect_halurust(root, halu_source, local_files, index, counts, retained)
    collect_rustmizan(
        mizan_source, mizan, local_mizan, lock, upstream_files,
        index, counts, differences, retained,
    )
    matches = find_intersections(index)
    return matches, counts, differences, retained, lock
