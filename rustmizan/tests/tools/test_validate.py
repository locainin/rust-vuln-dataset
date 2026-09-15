import importlib.util
import copy
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('rustmizan_validate', Path(__file__).resolve().parents[2] / 'tools/validate.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.fixture
def sample(tmp_path):
    project = tmp_path / 'samples/vuln-0001/sample-00001-function'
    (project / 'src').mkdir(parents=True)
    (project / 'Cargo.toml').write_text('[package]\nname="sample-00001-function"\nversion="0.1.0"\n')
    (project / 'src/lib.rs').write_text('struct Item;\nimpl Item {\nfn value() {}\n}\n')
    record = dict(path_to_crate='vuln-0001/sample-00001-function', is_vulnerability=True,
                  cwe_type=['CWE-416'], vulnerable_functions={'src/lib.rs': ['impl Item']},
                  vulnerable_lines={'src/lib.rs': [2, 4]}, deps=[])
    metadata = {'general_information': {}, 'vulnerabilities': [{'id': 'vuln-0001', 'code_samples': [record]}]}
    (tmp_path / 'mizan.json').write_text(json.dumps(metadata))
    (tmp_path / 'Cargo.toml').write_text('[workspace]\nmembers=["samples/vuln-0001/sample-00001-function"]\n')
    return tmp_path, metadata, record


def test_accepts_impl_annotation_noncontiguous_lines_and_missing_levels(sample):
    root, _, _ = sample
    assert module.validate(root)['variants'] == 1


@pytest.mark.parametrize('change,error', [
    (lambda s: s.update(is_vulnerability=False), 'state mismatch'),
    (lambda s: s.update(vulnerable_lines={'src/lib.rs': [0]}), 'line position'),
    (lambda s: s.update(vulnerable_lines={'src/lib.rs': [5]}), 'line position'),
    (lambda s: s.update(vulnerable_lines={'../secret': [1]}), 'unsafe path'),
    (lambda s: s.update(vulnerable_functions={'src/lib.rs': ['fn absent()']}), 'missing signature'),
    (lambda s: s.update(deps=['absent']), 'missing dependency'),
])
def test_rejects_invalid_annotation_without_repair(sample, change, error):
    root, metadata, record = sample
    change(record)
    (root / 'mizan.json').write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match=error):
        module.validate(root)


def test_rejects_repeated_case(sample):
    root, metadata, _ = sample
    metadata['vulnerabilities'] *= 2
    (root / 'mizan.json').write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match='repeated case'):
        module.validate(root)


def test_rejects_symlink_even_when_target_is_inside_root(tmp_path):
    (tmp_path / 'target').write_text('data')
    (tmp_path / 'link').symlink_to('target')
    with pytest.raises(ValueError, match='linked path'):
        module.contained(tmp_path, 'link')


def test_rejects_unlisted_file_in_integrity_inventory(tmp_path):
    (tmp_path / 'checksums.sha256').write_text('')
    (tmp_path / 'unexpected.rs').write_text('fn extra() {}')
    with pytest.raises(ValueError, match='inventory coverage'):
        module.verify_integrity(tmp_path)


def test_rejects_duplicate_inventory_path(tmp_path):
    import hashlib
    data = b'original'
    (tmp_path / 'source.rs').write_bytes(data)
    row = hashlib.sha256(data).hexdigest() + '  source.rs\n'
    (tmp_path / 'checksums.sha256').write_text(row * 2)
    with pytest.raises(ValueError, match='duplicate inventory'):
        module.verify_integrity(tmp_path)


def test_rejects_modified_source_bytes(tmp_path):
    import hashlib
    (tmp_path / 'source.rs').write_bytes(b'changed')
    (tmp_path / 'checksums.sha256').write_text(hashlib.sha256(b'original').hexdigest() + '  source.rs\n')
    with pytest.raises(ValueError, match='integrity mismatch'):
        module.verify_integrity(tmp_path)


def test_rejects_omitted_upstream_fixed_variant(sample, tmp_path):
    root, metadata, record = sample
    upstream = tmp_path / 'upstream'
    upstream.mkdir()
    original = copy.deepcopy(metadata)
    fixed = copy.deepcopy(record)
    fixed.update(path_to_crate='vuln-0001/sample-10001-function', is_vulnerability=False)
    original['vulnerabilities'][0]['code_samples'].append(fixed)
    (upstream / 'mizan.json').write_text(json.dumps(original))
    with pytest.raises(ValueError, match='annotation differs'):
        module.validate(root, upstream)


def test_rejects_changed_annotation_against_upstream(sample, tmp_path):
    root, metadata, record = sample
    upstream = tmp_path / 'upstream'
    upstream.mkdir()
    (upstream / 'mizan.json').write_text(json.dumps(metadata))
    record['vulnerable_lines']['src/lib.rs'] = [2]
    (root / 'mizan.json').write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match='annotation differs'):
        module.validate(root, upstream)


def test_rejects_root_workspace_override(sample):
    root, _, _ = sample
    with (root / 'Cargo.toml').open('a') as stream:
        stream.write('\n[patch.crates-io]\nhelper = { path = "../outside" }\n')
    with pytest.raises(ValueError, match='root workspace'):
        module.validate(root)


def test_rejects_linked_metadata_before_reading(sample):
    root, _, _ = sample
    path = root / 'mizan.json'
    path.rename(root / 'original.json')
    path.symlink_to('original.json')
    with pytest.raises(ValueError, match='linked path'):
        module.validate(root)


def test_rejects_unlisted_dependency(sample):
    root, _, _ = sample
    (root / 'samples/deps/extra').mkdir(parents=True)
    with pytest.raises(ValueError, match='dependency inventory'):
        module.validate(root)
