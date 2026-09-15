"""Read-only checks for native RustMizan projects and annotations."""

import argparse
import hashlib
import json
import re
import subprocess
import tomllib
from collections import Counter
from pathlib import Path

import yaml


def contained(root, relative):
    # Reject traversal and links before opening imported paths
    part = Path(relative)
    if part.is_absolute() or '..' in part.parts or not part.parts:
        raise ValueError(f'unsafe path: {relative}')
    path = root / part
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'escaping path: {relative}')
    current = root
    for name in part.parts:
        current = current / name
        if current.is_symlink():
            raise ValueError(f'linked path: {relative}')
    return path


def validate(root, upstream=None):
    # Reject links before any metadata or project read
    for path in [root, *root.rglob('*')]:
        if path.is_symlink():
            raise ValueError(f'linked path: {path}')
    metadata = json.loads((root / 'mizan.json').read_text())
    source = None
    if upstream is not None:
        source = json.loads((upstream / 'mizan.json').read_text())
        if {k: v for k, v in metadata.items() if k != 'vulnerabilities'} != {k: v for k, v in source.items() if k != 'vulnerabilities'}:
            raise ValueError('general information differs from upstream')
        source = {case['id']: case for case in source['vulnerabilities']}
    cases, samples, counts = set(), set(), Counter()
    dependencies = set()
    for case in metadata['vulnerabilities']:
        case_id = case['id']
        if not re.fullmatch(r'vuln-\d{4}', case_id) or case_id in cases:
            raise ValueError(f'invalid or repeated case: {case_id}')
        cases.add(case_id)
        if source is not None and source.get(case_id) != case:
            raise ValueError(f'annotation differs from upstream: {case_id}')
        if not case['code_samples']:
            raise ValueError(f'empty case: {case_id}')
        for sample in case['code_samples']:
            name = sample['path_to_crate']
            match = re.fullmatch(r'(vuln-(\d{4}))/sample-([01])(\d{4})-(crate|file|function)', name)
            if not match or match[1] != case_id or match[2] != match[4] or name in samples:
                raise ValueError(f'invalid or repeated sample: {name}')
            samples.add(name)
            label = sample['is_vulnerability']
            if type(label) is not bool or label != (match[3] == '0'):
                raise ValueError(f'state mismatch: {name}')
            counts[f'{"vulnerable" if label else "fixed"}_{match[5]}'] += 1
            project = contained(root / 'samples', name)
            tomllib.loads((project / 'Cargo.toml').read_text())
            cwes = sample['cwe_type']
            if not isinstance(cwes, list) or any(not re.fullmatch(r'CWE-\d+', cwe) for cwe in cwes):
                raise ValueError(f'invalid CWE: {name}')
            if label and not cwes:
                raise ValueError(f'missing vulnerable CWE: {name}')
            for dependency in sample['deps']:
                dependencies.add(dependency)
                dep = contained(root / 'samples/deps', dependency)
                if not (dep / 'Cargo.toml').is_file():
                    raise ValueError(f'missing dependency: {name}: {dependency}')
            for field in ('vulnerable_functions', 'vulnerable_lines'):
                for relative, annotations in sample[field].items():
                    text = contained(project, relative).read_text()
                    if field == 'vulnerable_lines':
                        length = len(text.splitlines())
                        if any(type(line) is not int or not 1 <= line <= length for line in annotations):
                            raise ValueError(f'invalid line position: {name}: {relative}')
                    else:
                        # Ignore spacing only, retaining non-function constructs
                        compact = re.sub(r'\s+', '', text)
                        if any(not signature.strip() or re.sub(r'\s+', '', signature) not in compact for signature in annotations):
                            raise ValueError(f'missing signature: {name}: {relative}')
            if not label and any(sample[key] for key in ('cwe_type', 'vulnerable_functions', 'vulnerable_lines')):
                raise ValueError(f'fixed-side annotation conflict: {name}')
    # The workspace must list exactly the retained sample projects
    cargo = tomllib.loads((root / 'Cargo.toml').read_text())
    if set(cargo) != {'workspace'} or set(cargo['workspace']) - {'resolver', 'members'}:
        raise ValueError('unexpected root workspace settings')
    workspace = cargo['workspace']
    if sorted(workspace['members']) != sorted(f'samples/{name}' for name in samples):
        raise ValueError('workspace member mismatch')
    if {str(p.parent.relative_to(root / 'samples')) for p in (root / 'samples').glob('vuln-*/sample-*/Cargo.toml')} != samples:
        raise ValueError('unlisted or missing sample directory')
    if {p.name for p in (root / 'samples/deps').glob('*') if p.is_dir()} != dependencies:
        raise ValueError('dependency inventory mismatch')
    # Check all local Cargo dependency paths, including transitive helpers
    for manifest in (root / 'samples').rglob('Cargo.toml'):
        data = tomllib.loads(manifest.read_text())
        def check_paths(value):
            if isinstance(value, dict):
                if isinstance(value.get('path'), str):
                    target = (manifest.parent / value['path']).resolve()
                    if not target.is_relative_to(root.resolve()) or not target.exists():
                        raise ValueError(f'missing or escaping Cargo path: {manifest}: {value["path"]}')
                for item in value.values():
                    check_paths(item)
            elif isinstance(value, list):
                for item in value:
                    check_paths(item)
        check_paths(data)
    return {'cases': len(cases), 'variants': len(samples), 'states_and_levels': dict(sorted(counts.items()))}


def verify_integrity(root, upstream=None):
    # Inventory covers source and integration files without hashing itself
    inventory = root / 'checksums.sha256'
    seen = set()
    for row in inventory.read_text().splitlines():
        digest, relative = row.split('  ', 1)
        if relative in seen:
            raise ValueError(f'duplicate inventory path: {relative}')
        seen.add(relative)
        data = contained(root, relative).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f'integrity mismatch: {relative}')
        if upstream is not None and relative.startswith('samples/'):
            if data != contained(upstream, relative).read_bytes():
                raise ValueError(f'source bytes changed: {relative}')
    actual = set()
    for path in root.rglob('*'):
        relative = str(path.relative_to(root))
        if path.is_symlink():
            raise ValueError(f'linked path: {relative}')
        if path.is_file() and relative not in {'checksums.sha256', 'source-lock.yaml'}:
            actual.add(relative)
    if actual != seen:
        raise ValueError(f'inventory coverage mismatch: {sorted(actual ^ seen)}')


def verify_provenance(root, upstream):
    lock = yaml.safe_load((root / 'source-lock.yaml').read_text())
    revision = subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != lock['upstream']['revision']:
        raise ValueError('upstream revision mismatch')
    if subprocess.check_output(['git', '-C', str(upstream), 'status', '--porcelain', '--untracked-files=no'], text=True).strip():
        raise ValueError('upstream tracked files are modified')
    if hashlib.sha256((upstream / 'mizan.json').read_bytes()).hexdigest() != lock['upstream']['metadata_sha256']:
        raise ValueError('upstream metadata hash mismatch')
    if (root / 'rust-toolchain.toml').read_bytes() != (upstream / 'rust-toolchain.toml').read_bytes():
        raise ValueError('toolchain pin changed')
    source = json.loads((upstream / 'mizan.json').read_text())
    current = json.loads((root / 'mizan.json').read_text())
    decisions = lock['cases']
    if set(decisions) != {case['id'] for case in source['vulnerabilities']}:
        raise ValueError('case disposition coverage mismatch')
    included = {key for key, value in decisions.items() if value['disposition'] == 'included'}
    if included != {case['id'] for case in current['vulnerabilities']}:
        raise ValueError('included case mismatch')
    for case in current['vulnerabilities']:
        expected = {sample['path_to_crate'] for sample in case['code_samples']}
        evidence = decisions[case['id']]['builds']
        if set(evidence) != expected or any(result != 'pass' for result in evidence.values()):
            raise ValueError('missing successful build evidence')
    # A filtered lock may remove packages, never silently resolve new versions
    identity = lambda package: (package['name'], package['version'], package.get('source'), package.get('checksum'))
    original = {identity(p) for p in tomllib.loads((upstream / 'Cargo.lock').read_text())['package']}
    imported = {identity(p) for p in tomllib.loads((root / 'Cargo.lock').read_text())['package']}
    if imported - original:
        raise ValueError('dependency lock introduced new resolutions')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--upstream', type=Path, required=True)
    args = parser.parse_args()
    result = validate(args.root, args.upstream)
    verify_integrity(args.root, args.upstream)
    verify_provenance(args.root, args.upstream)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
