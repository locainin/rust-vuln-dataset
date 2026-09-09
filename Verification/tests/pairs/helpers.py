# Small pair fixtures shared by focused validation checks

BEFORE = "fn helper() {}\n\n    pub fn sample() {\n        vulnerable_call();\n    }\n"
AFTER = "fn helper() {}\n\n    pub fn sample() {\n        fixed_call();\n    }\n"
VULNERABLE = "    pub fn sample() {\n        vulnerable_call();\n    }\n"
FIXED = "    pub fn sample() {\n        fixed_call();\n    }\n"
NORMALIZED_VULNERABLE = "pub fn sample() {\n    vulnerable_call();\n}\n"
NORMALIZED_FIXED = "pub fn sample() {\n    fixed_call();\n}\n"


def make_case(tmp_path):
    case_dir = tmp_path / "RUSTSEC-2099-0001"
    (case_dir / "pairs").mkdir(parents=True)
    (case_dir / "metadata.yaml").write_text(
        "id: RUSTSEC-2099-0001\n",
        encoding="utf-8",
    )
    return case_dir


def make_pair(pair_dir):
    pair_dir.mkdir(parents=True)
    for filename, text in (
        ("before.rs", BEFORE),
        ("after.rs", AFTER),
        ("vulnerable.rs", VULNERABLE),
        ("fixed.rs", FIXED),
    ):
        (pair_dir / filename).write_text(text, encoding="utf-8")
