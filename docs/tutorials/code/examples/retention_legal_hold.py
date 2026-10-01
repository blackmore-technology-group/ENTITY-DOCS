from pathlib import Path
import importlib.util, hashlib, os, shutil
ROOT=Path(os.environ.get("ENTITY_ROOT",Path.cwd())).resolve()
STATE=ROOT/".tutorial-test-state"/"retention-legal-hold"
if STATE.exists(): shutil.rmtree(STATE)
def load_source(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
identity_mod=load_source("src/01_Core_Runtime/identity/canonical_identity.py","entity_identity")
privacy=load_source("src/35_Global_Infrastructure/privacy_provenance.py","entity_privacy")
identity=identity_mod.EntityIdentityVault(STATE); owner=identity.create("Retention Owner","organization")
ledger=privacy.SelectiveRetentionLedger(STATE,identity)
payload_hash=hashlib.sha256(b"personal tutorial payload").hexdigest()
rec=ledger.register(owner["entity_id"],"subject:tutorial",payload_hash,purpose="RESEARCH",jurisdiction="CA-BC",retain_until_ms=1,destruction_mode="DELETE_PAYLOAD")
destroyed=ledger.destroy(owner["entity_id"],rec["record_id"],hashlib.sha256(b"destroyed").hexdigest())
status=ledger.status(rec["record_id"]); assert destroyed["status"]=="DESTROYED" and status["commitment_preserved"]
hold=ledger.register(owner["entity_id"],"subject:legal",payload_hash,purpose="LEGAL",jurisdiction="CA",retain_until_ms=1,destruction_mode="LEGAL_HOLD")
blocked="NOT_BLOCKED"
try: ledger.destroy(owner["entity_id"],hold["record_id"],hashlib.sha256(b"x").hexdigest())
except PermissionError: blocked="BLOCKED"
assert blocked=="BLOCKED"
print("DESTRUCTION=PASS"); print("COMMITMENT_PRESERVED=PASS"); print("LEGAL_HOLD_DESTRUCTION=BLOCKED")
print("CLAIM_BOUNDARY=retention evidence does not prove remote copies were erased")
