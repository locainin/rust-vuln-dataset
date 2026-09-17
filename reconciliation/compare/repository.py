import os
import subprocess
import tempfile
from pathlib import Path


HALURUST_REPOSITORY = "https://github.com/Hambbburger/CVE_Samples"


HALURUST_REVISION = "b97396b4c2adcb1156b71c4d73ef358dcd5a9ebf"


def verify_checkout(path, revision):
    if not path.is_dir():
        raise ValueError(
            f"Directory does not exist: {path}\n"
            "Pass an actual checkout directory after each --*-source option.\n"
            "HALURUST_SOURCE and RUSTMIZAN_SOURCE are placeholders, not paths."
        )
    try:
        head = subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            text=True, stderr=subprocess.PIPE,
        ).strip()
        dirty = subprocess.check_output(
            ["git", "-C", str(path), "status", "--porcelain"],
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as error:
        raise ValueError(
            f"Not a readable Git checkout: {path}\n"
            "Use the upstream repository checkout, not a downloaded source folder.\n"
            f"Inspect it with: git -C {str(path)!r} status"
        ) from error
    if head != revision:
        raise ValueError(
            f"Wrong upstream revision: {path}\n"
            f"  Expected: {revision}\n"
            f"  Found:    {head}\n"
            "Use a separate clean checkout at the expected revision."
        )
    if dirty:
        raise ValueError(
            f"Upstream checkout has local changes: {path}\n"
            "Use a clean checkout; this script will not reset or discard files."
        )


def tracked_files(repository):
    output = subprocess.check_output(
        ["git", "-C", str(repository), "ls-tree", "-r", "--name-only", "-z", "HEAD"],
        stderr=subprocess.PIPE,
    )
    return {Path(os.fsdecode(name)) for name in output.split(b"\0") if name}


def require_tracked_file(repository, relative, tracked):
    relative = Path(relative)
    if relative not in tracked or not (repository / relative).is_file():
        raise ValueError(f"Missing tracked input: {repository / relative}")
    return repository / relative


def read_local_bytes(repository, relative, tracked):
    path = require_tracked_file(repository, relative, tracked)
    data = path.read_bytes()
    committed = subprocess.check_output(
        ["git", "-C", str(repository), "cat-file", "blob", f"HEAD:{Path(relative).as_posix()}"],
        stderr=subprocess.PIPE,
    )
    # Compare raw bytes, not diff output that may trust index flags or filters
    if data != committed:
        raise ValueError(
            f"Local comparison input differs from HEAD: {relative}\n"
            "Comparison stopped; no files were reset or restored."
        )
    return data


def prepare_checkout(family, source, override):
    if override is not None:
        verify_checkout(override, source["revision"])
        return override

    cache_home = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    cache = cache_home / "rustxec-reconciliation"
    destination = cache / f"{family}-{source['revision']}"
    if destination.exists():
        verify_checkout(destination, source["revision"])
        return destination

    cache.mkdir(parents=True, exist_ok=True)
    # Publish only complete checkouts; interrupted downloads never become the cache
    with tempfile.TemporaryDirectory(prefix="download-", dir=cache) as temporary:
        checkout = Path(temporary) / "source"
        commands = [
            ["git", "init", "--quiet", str(checkout)],
            ["git", "-C", str(checkout), "remote", "add", "origin", source["repository"]],
            ["git", "-C", str(checkout), "fetch", "--quiet", "--depth=1",
             "origin", source["revision"]],
            ["git", "-C", str(checkout), "-c", "core.hooksPath=/dev/null",
             "checkout", "--quiet", "--detach", "FETCH_HEAD"],
        ]
        environment = dict(os.environ, GIT_TERMINAL_PROMPT="0")
        for command in commands:
            try:
                subprocess.run(
                    command, check=True, capture_output=True, text=True,
                    env=environment, timeout=300,
                )
            except subprocess.CalledProcessError as error:
                detail = error.stderr.strip()
                raise ValueError(f"Could not download {family}: {detail}") from error
            except subprocess.TimeoutExpired as error:
                raise ValueError(
                    f"Downloading {family} timed out. Check the connection and rerun."
                ) from error
        verify_checkout(checkout, source["revision"])
        checkout.rename(destination)
    return destination
