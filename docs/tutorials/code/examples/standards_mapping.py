from pathlib import Path
import importlib.util, os
ROOT=Path(os.environ.get("ENTITY_ROOT",Path.cwd())).resolve()
def load_source(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
m=load_source("src/36_Adoption_Layer/standards_adapters.py","entity_standards")
odrl={"permission":[{"target":"dataset-123","action":["read","derive"],"duty":[{"action":"attribute"}]}],"prohibition":[{"target":"dataset-123","action":"redistribute"}]}
mapping=m.StandardsAdapters.import_odrl(odrl)
assert mapping["silent_semantic_equivalence"] is False
assert mapping["external_standard_is_not_entity_authority"] is True
vc={"issuer":"did:example:issuer","credentialSubject":{"id":"did:example:subject"},"proof":{"type":"ExampleProof"}}
vc_evidence=m.StandardsAdapters.credential_evidence(vc)
did_evidence=m.StandardsAdapters.did_evidence({"id":"did:example:subject","verificationMethod":[]})
assert vc_evidence["credential_is_evidence_not_entity_authority"] is True
assert did_evidence["external_identifier_is_not_entity_authority"] is True
roundtrip=m.StandardsAdapters.export_odrl(mapping["mapped_rights"],"dataset-123")
print("ODRL_IMPORT=PASS"); print(f"MAPPED_RIGHTS={len(mapping['mapped_rights'])}")
print("VC_AS_EVIDENCE=PASS"); print("DID_AS_EVIDENCE=PASS"); print("ODRL_EXPORT=PASS" if roundtrip else "ODRL_EXPORT=FAIL")
print("EXTERNAL_STANDARD_AUTHORITY=BLOCKED")
