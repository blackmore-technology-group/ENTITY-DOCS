from pathlib import Path
import os
import copy
import hashlib
import importlib.util
import shutil

ROOT = Path(os.environ.get("ENTITY_ROOT", Path.cwd())).resolve()
STATE = ROOT / ".tutorial-test-state" / "bundle-verification"
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
owner = identity.create("Bundle Owner", "organization")
researcher = identity.create("Bundle Researcher", "person")
fabric = fabric_mod.UniversalTransactionFabric(STATE, identity)
digest = hashlib.sha256(b"portable tutorial object").hexdigest()
obj = fabric.register_object(
    owner["entity_id"], "DOCUMENT", "Portable Tutorial Object",
    content_sha256=digest,
)
fabric.grant_right(
    obj["object_id"], owner["entity_id"], researcher["entity_id"],
    ["READ"], constraints={"purposes": ["tutorial"]},
)
bundle = fabric.export_bundle(obj["object_id"])
verification = fabric.verify_bundle(bundle)
assert verification["valid"] is True
assert verification["primitive_set_complete"] is True
assert verification["provider_independent"] is True

# Negative control: change governed data without recomputing signatures/hash.
tampered = copy.deepcopy(bundle)
tampered["objects"][0]["title"] = "Tampered title"
tampered_result = fabric.verify_bundle(tampered)
assert tampered_result["valid"] is False
assert "semantic_hash_invalid" in tampered_result["failures"]

print(f"ROOT_OBJECT={obj['object_id']}")
print(f"SEMANTIC_SHA256={bundle['semantic_sha256']}")
print(f"VERIFIED_MANIFESTS={verification['verified_manifest_count']}")
print("PORTABLE_BUNDLE_VERIFICATION=PASS")
print("TAMPER_NEGATIVE_CONTROL=BLOCKED")
print("CLAIM_BOUNDARY=verification proves bundle integrity/signatures, not external truth")
