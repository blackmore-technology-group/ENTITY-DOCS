from pathlib import Path
import importlib.util, hashlib, os, shutil
ROOT=Path(os.environ.get("ENTITY_ROOT",Path.cwd())).resolve()
STATE=ROOT/".tutorial-test-state"/"confidential-provenance"
if STATE.exists(): shutil.rmtree(STATE)
def load_source(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
identity_mod=load_source("src/01_Core_Runtime/identity/canonical_identity.py","entity_identity")
privacy=load_source("src/35_Global_Infrastructure/privacy_provenance.py","entity_privacy")
identity=identity_mod.EntityIdentityVault(STATE); owner=identity.create("Provenance Owner","organization")
ledger=privacy.ConfidentialProvenanceLedger(STATE,identity)
key=hashlib.sha256(b"tutorial-confidential-key").digest()
edge=ledger.add_edge(owner["entity_id"],"dataset:A","model:B","DERIVED_FROM",hashlib.sha256(b"evidence").hexdigest(),metadata={"private_detail":"sensitive lineage"},encryption_key=key)
revealed=ledger.reveal_metadata(edge["edge_id"],key)
assert revealed["commitment_valid"] and revealed["metadata"]["private_detail"]=="sensitive lineage"
wrong="NOT_BLOCKED"
try: ledger.reveal_metadata(edge["edge_id"],hashlib.sha256(b"wrong-key").digest())
except Exception: wrong="BLOCKED"
assert wrong=="BLOCKED"
print("CONFIDENTIAL_EDGE=PASS"); print("COMMITMENT_VERIFY=PASS"); print("WRONG_KEY_REVEAL=BLOCKED")
print("CLAIM_BOUNDARY=encrypted metadata commitment is provenance evidence, not universal truth")
