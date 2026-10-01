from pathlib import Path
import os
import hashlib
import importlib.util
import shutil

ROOT = Path(os.environ.get("ENTITY_ROOT", Path.cwd())).resolve()
STATE = ROOT / ".tutorial-test-state" / "rights-provenance"
if STATE.exists():
    shutil.rmtree(STATE)

def load_source(relative_path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

identity_mod = load_source(
    "src/01_Core_Runtime/identity/canonical_identity.py", "entity_identity"
)
fabric_mod = load_source(
    "src/30_Universal_Transaction_Fabric/canonical_universal_fabric.py",
    "entity_fabric",
)
identity = identity_mod.EntityIdentityVault(STATE)
owner = identity.create("Tutorial Owner", "organization")
operator = identity.create("Tutorial Operator", "person")
researcher = identity.create("Tutorial Researcher", "person")
fabric = fabric_mod.UniversalTransactionFabric(STATE, identity)
source_digest = hashlib.sha256(b"tutorial source dataset").hexdigest()
source = fabric.register_object(
    owner["entity_id"], "DATASET", "Tutorial Source Dataset",
    content_sha256=source_digest,
)
authority = fabric.delegate_authority(
    source["object_id"], owner["entity_id"], operator["entity_id"],
    ["LICENSE", "PUBLISH"], scope={"channel": "research"},
)
assert fabric.active_authority(
    source["object_id"], operator["entity_id"], "LICENSE"
)
assert fabric.active_authority(
    source["object_id"], operator["entity_id"], "SETTLE"
) is None

right = fabric.grant_right(
    source["object_id"], owner["entity_id"], researcher["entity_id"],
    ["READ", "TRAIN"],
    constraints={"purposes": ["research"], "jurisdictions": ["CA"]},
)
assert fabric.active_right(
    source["object_id"], researcher["entity_id"], "TRAIN",
    purpose="research", jurisdiction="CA",
)
assert fabric.active_right(
    source["object_id"], researcher["entity_id"], "COMMERCIALIZE",
    purpose="research", jurisdiction="CA",
) is None

derived_digest = hashlib.sha256(b"tutorial derived dataset").hexdigest()
derived = fabric.register_object(
    owner["entity_id"], "DATASET", "Tutorial Derived Dataset",
    content_sha256=derived_digest,
)
edge = fabric.add_provenance(
    owner["entity_id"], source["object_id"], derived["object_id"],
    "DERIVED_FROM", contribution_bps=7000,
    evidence={"note": "tutorial deterministic lineage"},
)
distribution = fabric.contribution_distribution(derived["object_id"], 100)
assert distribution["allocated_total"] == 100
assert distribution["root_contribution_bps"][source["object_id"]] == 7000
assert distribution["root_contribution_bps"][derived["object_id"]] == 3000

print(f"SOURCE_OBJECT={source['object_id']}")
print(f"DERIVED_OBJECT={derived['object_id']}")
print("LICENSE_AUTHORITY=PASS")
print("UNGRANTED_SETTLE_AUTHORITY=BLOCKED")
print("TRAIN_RIGHT=PASS")
print("UNGRANTED_COMMERCIALIZE_RIGHT=BLOCKED")
print(f"PROVENANCE_EDGE={edge['edge_id']}")
print("VALUE_DISTRIBUTION=70_SOURCE/30_DERIVED")
print("CLAIM_BOUNDARY=provenance is not ownership; allocation is deterministic model output")
