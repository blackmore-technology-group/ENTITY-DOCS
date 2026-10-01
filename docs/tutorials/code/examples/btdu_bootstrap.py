from pathlib import Path
import os
import importlib.util
import shutil

ROOT = Path(os.environ.get("ENTITY_ROOT", Path.cwd())).resolve()
STATE = ROOT / ".tutorial-btdu" / "entity"
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
vault = identity_mod.EntityIdentityVault(STATE)
manifest = vault.create(
    display_name="BTDU Tutorial Owner",
    entity_type="organization",
    aliases=["btdu-tutorial-owner"],
    metadata={"purpose": "disposable BTDU tutorial"},
)
assert identity_mod.EntityIdentityVault.verify_manifest(manifest)
print(manifest["entity_id"])
