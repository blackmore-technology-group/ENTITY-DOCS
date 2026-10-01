from pathlib import Path
import os
import hashlib
import importlib.util
import shutil

ROOT = Path(os.environ.get("ENTITY_ROOT", Path.cwd())).resolve()
STATE = ROOT / ".tutorial-test-state" / "evidence-trust"
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
owner = identity.create("Trust Policy Owner", "organization")
attestor_a = identity.create("Attestor A", "organization")
attestor_b = identity.create("Attestor B", "organization")
fabric = fabric_mod.UniversalTransactionFabric(STATE, identity)
subject = fabric.register_object(
    owner["entity_id"],
    "DOCUMENT",
    "Tutorial Evidence Subject",
    content_sha256=hashlib.sha256(b"evidence subject").hexdigest(),
)
policy = fabric.create_trust_policy(
    owner["entity_id"],
    "QUALITY_CHECK",
    minimum_attestations=2,
    allowed_attestors=[attestor_a["entity_id"], attestor_b["entity_id"]],
)

first_evidence = hashlib.sha256(b"attestor A evidence").hexdigest()
fabric.attest(
    attestor_a["entity_id"],
    subject["object_id"],
    "QUALITY_CHECK",
    first_evidence,
    claim={"result": "PASS", "scope": "tutorial"},
)
first_eval = fabric.evaluate_trust(policy["policy_id"], subject["object_id"])
assert first_eval["policy_satisfied"] is False
assert first_eval["valid_attestation_count"] == 1
second_evidence = hashlib.sha256(b"attestor B evidence").hexdigest()
fabric.attest(
    attestor_b["entity_id"],
    subject["object_id"],
    "QUALITY_CHECK",
    second_evidence,
    claim={"result": "PASS", "scope": "tutorial"},
)
second_eval = fabric.evaluate_trust(policy["policy_id"], subject["object_id"])
assert second_eval["policy_satisfied"] is True
assert second_eval["valid_attestation_count"] == 2
assert second_eval["truth_inferred"] is False

print(f"SUBJECT={subject['object_id']}")
print("ONE_ATTESTATION_POLICY=NOT_SATISFIED")
print("TWO_ATTESTATION_POLICY=SATISFIED")
print("VALID_ATTESTATIONS=2")
print("TRUTH_INFERRED=FALSE")
print("CLAIM_BOUNDARY=policy satisfaction evaluates evidence, not objective truth")
