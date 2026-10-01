from pathlib import Path
import hashlib, json, shutil, sqlite3, sys, tarfile

ADAM_PACKAGE = Path(r"E:\ENTITY_ACTIVE\BTG_BUILT_LOCALAPPDATA\BTG\ADAM_RC2\ADAM_v1_0_COMPLETE_SOFTWARE_REFERENCE_RC2")
BASE = Path(r"E:\ENTITY_ACTIVE\EXTERNAL_CONTRIBUTIONS\evidence\memnox-46\ENTITY_FULL_SOURCE_STATE\9c788e73b53f-40FFD74F238A77A9")
RECEIPT = Path(r"E:\ENTITY_ACTIVE\EXTERNAL_CONTRIBUTIONS\evidence\memnox-46\memnox-46-btdu-cold-recovery-qualified-receipt.json")
OUT = Path(r"E:\ENTITY_ACTIVE\ENTITY_TESTING_20261001\runs\memnox-cold-recovery")
sys.path.insert(0, str(ADAM_PACKAGE))
from adam_v41.universe import AtomicUniverse
from adam_v41.exact import ExactCodec

if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True)
receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
sealed = BASE / "adam" / "entity_atomic_universe"
log = sealed / "universe.a41log"
log_size_before = log.stat().st_size
u = AtomicUniverse(sealed)
codec = ExactCodec(u)
assert u.root_hash == receipt["signed_adam_verification"]["final_root"]
index = sqlite3.connect(BASE / "btdu_index.sqlite")
targets = {
    "archive": ("memnox-accepted.tar", "application/x-tar"),
    "manifest": ("memnox-accepted-source-manifest.json", "application/json"),
    "acceptance_receipt": ("memnox-acceptance-receipt.json", "application/json"),
}
files = {}
for name, (filename, media_type) in targets.items():
    expected = receipt["cold_recovery"]["objects"][name]
    row = index.execute(
        "select evidence_object_id,content_sha256,size_bytes from objects where lower(content_sha256)=?",
        (expected["sha256"].lower(),),
    ).fetchone()
    assert row is not None
    exact_object_id, indexed_sha, indexed_size = row
    assert indexed_sha.lower() == expected["sha256"].lower()
    assert indexed_size == expected["bytes"]
    data = codec.reconstruct(exact_object_id)
    assert len(data) == expected["bytes"]
    assert hashlib.sha256(data).hexdigest().upper() == expected["sha256"]
    dest = OUT / filename
    dest.write_bytes(data)
    files[name] = dest
manifest = json.loads(files["manifest"].read_text(encoding="utf-8"))
tree = OUT / "tree"
tree.mkdir()
with tarfile.open(files["archive"], "r:") as tf:
    tf.extractall(tree, filter="data")
expected = {e["path"]: e for e in manifest["tracked_entries"] if e["type"] == "blob"}
actual = {str(p.relative_to(tree)).replace("\\", "/"): p for p in tree.rglob("*") if p.is_file()}
missing = sorted(set(expected) - set(actual))
extra = sorted(set(actual) - set(expected))
mismatched = []
for path, entry in expected.items():
    if path not in actual: continue
    data = actual[path].read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()
    if blob != entry["object_sha1"] or len(data) != entry["size"]:
        mismatched.append(path)
verified = len(expected) - len(missing) - len(mismatched)
assert not missing and not extra and not mismatched
assert verified == receipt["cold_recovery"]["tracked_git_blobs_expected"] == 865
assert log.stat().st_size == log_size_before == receipt["signed_adam_verification"]["log_bytes_before"]
print("MEMNOX_COLD_RECOVERY=PASS")
print(f"SEALED_ADAM_ROOT={u.root_hash}")
print(f"TRACKED_GIT_BLOBS={verified}/{len(expected)}")
print(f"MISSING_PATHS={len(missing)}")
print(f"EXTRA_PATHS={len(extra)}")
print(f"GIT_BLOB_MISMATCHES={len(mismatched)}")
print("GIT_INVOKED=FALSE")
print("GITHUB_INVOKED=FALSE")
print("NETWORK_REQUIRED=FALSE")
print("SOURCE_CLONE_READ=FALSE")
print(f"SEALED_LOG_BYTES_UNCHANGED={log.stat().st_size}")
print("CLAIM_BOUNDARY=PASS applies to this qualified 865-blob corpus and sealed BTDU recovery path")
