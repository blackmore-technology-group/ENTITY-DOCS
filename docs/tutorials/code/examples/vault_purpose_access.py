from pathlib import Path
import importlib.util, hashlib, os, shutil, time
ROOT=Path(os.environ.get("ENTITY_ROOT", Path.cwd())).resolve()
STATE=ROOT/".tutorial-test-state"/"vault-purpose-access"
if STATE.exists(): shutil.rmtree(STATE)
def load_source(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
identity_mod=load_source("src/01_Core_Runtime/identity/canonical_identity.py","entity_identity")
vault_mod=load_source("src/08_Data_Vaults/canonical_encrypted_vault.py","entity_vault")
privacy_mod=load_source("src/35_Global_Infrastructure/privacy_provenance.py","entity_privacy")
identity=identity_mod.EntityIdentityVault(STATE)
owner=identity.create("Tutorial Owner","organization"); reader=identity.create("Tutorial Reader","person")
vault=vault_mod.EncryptedDataVault(STATE)
item=vault.put_bytes(owner["entity_id"],b"confidential tutorial payload",media_type="text/plain",classification="PRIVATE")
assert vault.read_bytes(owner["entity_id"],item["vault_object_id"]) == b"confidential tutorial payload"
access=privacy_mod.PurposeBoundAccessRegistry(STATE,identity)
grant=access.grant(owner["entity_id"],reader["entity_id"],item["vault_object_id"],purposes=["RESEARCH"],actions=["READ"],expires_at_ms=int(time.time()*1000)+60000,max_uses=1)
use_hash=hashlib.sha256(b"tutorial-read-session").hexdigest(); use=access.authorize_use(grant["grant_id"],reader["entity_id"],"RESEARCH","READ",use_hash)
assert use["authorized"] is True and use["remaining_uses"] == 0
second="NOT_BLOCKED"
try: access.authorize_use(grant["grant_id"],reader["entity_id"],"RESEARCH","READ",use_hash)
except PermissionError: second="BLOCKED"
assert second=="BLOCKED"
print(f"VAULT_OBJECT={item['vault_object_id']}"); print("OWNER_READ=PASS"); print("PURPOSE_BOUND_READ=PASS"); print("SECOND_USE=BLOCKED"); print("CLAIM_BOUNDARY=encrypted custody and bounded access do not establish ownership")
