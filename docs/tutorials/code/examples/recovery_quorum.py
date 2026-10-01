from pathlib import Path
import importlib.util, os, shutil
ROOT=Path(os.environ.get("ENTITY_ROOT",Path.cwd())).resolve()
STATE=ROOT/".tutorial-test-state"/"recovery-quorum"
if STATE.exists(): shutil.rmtree(STATE)
def load_source(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
identity_mod=load_source("src/01_Core_Runtime/identity/canonical_identity.py","entity_identity")
hardening=load_source("src/32_V3_Hardening/hardening_profiles.py","entity_hardening")
identity=identity_mod.EntityIdentityVault(STATE)
target=identity.create("Recovery Target","organization")
a=identity.create("Approver A","person"); b=identity.create("Approver B","person"); c=identity.create("Approver C","person"); outsider=identity.create("Outsider","person")
q=hardening.RecoveryQuorum(STATE,identity)
q.set_policy(target["entity_id"],[a["entity_id"],b["entity_id"],c["entity_id"]],2)
req=q.request(target["entity_id"],"tutorial recovery")
q.approve(req["request_id"],a["entity_id"]); first=q.ready(req["request_id"]); assert first["ready"] is False
blocked="NOT_BLOCKED"
try: q.approve(req["request_id"],outsider["entity_id"])
except PermissionError: blocked="BLOCKED"
q.approve(req["request_id"],b["entity_id"]); second=q.ready(req["request_id"])
assert blocked=="BLOCKED" and second["ready"] is True and second["approval_count"]==2
print("RECOVERY_POLICY=2_OF_3"); print("ONE_APPROVAL_READY=FALSE"); print("UNAUTHORIZED_APPROVER=BLOCKED"); print("TWO_APPROVALS_READY=TRUE")
print("CLAIM_BOUNDARY=quorum readiness authorizes recovery workflow; it does not itself restore external systems")
