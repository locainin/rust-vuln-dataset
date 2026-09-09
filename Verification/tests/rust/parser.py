# Regression checks for local Rust syntax parsing and item boundaries

import subprocess

import pytest

from Verification.verifier.rust.parser import (
    item_at,
    rust_nodes,
)


def check_ast_grep_timeout_is_reported(monkeypatch):
    def timeout(command, **options):
        raise subprocess.TimeoutExpired(command, options["timeout"])

    monkeypatch.setattr("Verification.verifier.rust.parser.subprocess.run", timeout)
    rust_nodes.cache_clear()

    with pytest.raises(ValueError, match="ast-grep.*timed out.*45 seconds"):
        rust_nodes(b"fn helper() {}\n")


def check_complete_attributed_item():
    blob = b"#[inline]\nfn helper() {}\n"
    node = item_at(blob, 0, len(blob))

    assert node is not None
    assert node["ruleId"] == "item"
    assert node["text"] == "fn helper() {}"


def check_item_parser_rejects_partial_byte_range():
    blob = b"fn helper() {}\n"
    node = next(node for node in rust_nodes(blob) if node["ruleId"] == "item")
    bounds = node["range"]["byteOffset"]

    assert item_at(blob, bounds["start"], bounds["end"] - 1) is None
