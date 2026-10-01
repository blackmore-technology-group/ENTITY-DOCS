from pathlib import Path
import importlib.util, hashlib, os, shutil
ROOT=Path(os.environ.get("ENTITY_ROOT", Path.cwd())).resolve(); STATE=ROOT/".tutorial-test-state"/"rights-global-passport"
if STATE.exists(): shutil.rmtree(STATE)
def load_source(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
identity_mod=load_source("src/01_Core_Runtime/identity/canonical_identity.py","entity_identity")
fabric_mod=load_source("src/30_Universal_Transaction_Fabric/canonical_universal_fabric.py","entity_fabric")
rights_mod=load_source("src/36_Adoption_Layer/rights_passport.py","entity_rights_passport")
profiles_mod=load_source("src/38_Global_Passports/profile_registry.py","entity_profiles")
global_mod=load_source("src/38_Global_Passports/global_passport.py","entity_global_passport")
identity=identity_mod.EntityIdentityVault(STATE); owner=identity.create("Tutorial Owner","organization")
fabric=fabric_mod.UniversalTransactionFabric(STATE,identity); obj=fabric.register_object(owner["entity_id"],"DATASET","Tutorial Passport Dataset")
rights=rights_mod.RightsPassportRegistry(STATE,identity,fabric); rp=rights.issue(owner["entity_id"],obj["object_id"],rights=[{"effect":"ALLOW","actions":["READ"],"conditions":{},"obligations":[],"right_refs":[]}],privacy_profile="SELECTIVE_DISCLOSURE")
assert rights.verify(rp)["valid"] is True
profiles=profiles_mod.GlobalProfileRegistry(STATE,identity); schema_sha=hashlib.sha256(b"tutorial-global-profile-v1").hexdigest(); profile=profiles.register(owner["entity_id"],"entity-profile:tutorial-global","1.0","GLOBAL",schema_sha256=schema_sha,object_types=["DATASET"],required_evidence_types=["DOCUMENT"],policy={"tutorial":True})
assert profiles.verify(profile)["valid"] is True
global_registry=global_mod.GlobalPassportRegistry(STATE,identity,fabric,rights,profiles); gp=global_registry.issue(owner["entity_id"],obj["object_id"],rp["passport_id"],profile_refs=[profile["profile_ref"]],economic_state={"state":"POTENTIAL","amount_units":0,"currency":"CAD"})
assert global_registry.verify(gp)["valid"] is True
print(f"OBJECT={obj['object_id']}"); print(f"RIGHTS_PASSPORT={rp['passport_id']}"); print(f"GLOBAL_PASSPORT={gp['passport_id']}"); print("RIGHTS_PASSPORT_VERIFY=PASS"); print("GLOBAL_PASSPORT_VERIFY=PASS"); print("ECONOMIC_STATE=POTENTIAL_0_CAD"); print("CLAIM_BOUNDARY=passport composition does not create new authority or realized value")
