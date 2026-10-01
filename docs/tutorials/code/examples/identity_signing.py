from pathlib import Path
import os
import importlib.util
import shutil

ROOT = Path(os.environ.get("ENTITY_ROOT", Path.cwd())).resolve()
STATE = ROOT / ".tutorial-test-state" / "identity-signing"
if STATE.exists():
    shutil.rmtree(STATE)

def load_source(relative_path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

identity_mod = load_source(
    "src/01_Core_Runtime/identity/canonical_identity.py",
    "entity_identity",
)
vault = identity_mod.EntityIdentityVault(STATE)
manifest = vault.create(
    display_name="Tutorial Developer",
    entity_type="person",
    aliases=["tutorial-developer"],
    metadata={"purpose": "ENTITY code tutorial"},
)
entity_id = manifest["entity_id"]
assert identity_mod.EntityIdentityVault.verify_manifest(manifest)
payload = {
    "action": "TUTORIAL_ASSERTION",
    "subject": "example-object",
    "statement": "Signed by the tutorial ENTITY identity",
}
signature = vault.sign(entity_id, payload)
assert identity_mod.EntityIdentityVault.verify_signature(
    manifest,
    payload,
    signature,
)
rotated = vault.rotate_signing_key(entity_id)
assert identity_mod.EntityIdentityVault.verify_manifest(rotated)

print(f"ENTITY_ID={entity_id}")
print("MANIFEST_VERIFIED=PASS")
print("PAYLOAD_SIGNATURE=PASS")
print("KEY_ROTATION_CONTINUITY=PASS")
print("CLAIM_BOUNDARY=signature proves key control, not truth or ownership")
