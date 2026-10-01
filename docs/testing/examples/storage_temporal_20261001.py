from pathlib import Path
import sys, json, shutil
INSTALLED=Path(r'E:\ENTITY_ACTIVE\BTG_BUILT_LOCALAPPDATA\BTG\ADAM_RC2\ADAM_v1_0_COMPLETE_SOFTWARE_REFERENCE_RC2')
OUT=Path(r'E:\ENTITY_ACTIVE\ENTITY_STORAGE_SCENARIOS_20261001\temporal_cycle_regression')
sys.path.insert(0,str(INSTALLED))
from adam_v41.universe import AtomicUniverse
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True)
u=AtomicUniverse(OUT/'adam')
eid,_=u.assert_entity('project','P-1',{'status':'active','note':'initial','cost':100})
initial_seq=u.sequence; expected=u.entity_view(eid,at_seq=initial_seq)
for step in range(1,11):
    facts={'status':['active','review','approved','closed'][step%4],'note':f'update-{step%5}','cost':100+step}
    u.assert_entity('project','P-1',facts,expected_version=u.entity_versions[eid])
actual=u.entity_view(eid,at_seq=initial_seq); latest=u.entity_view(eid); verify=u.verify()
diff={k:{'expected':expected.get(k),'actual':actual.get(k)} for k in sorted(set(expected)|set(actual)) if expected.get(k)!=actual.get(k)}
gap=bool(actual!=expected and verify['pass'] and latest.get('cost')==110)
result={'scenario':'temporal-cycle-regression','updates':10,'initial_seq':initial_seq,'expected_initial_view':expected,'actual_historical_view_after_cycles':actual,'latest_view':latest,'differences':diff,'integrity':verify['pass'],'gap_reproduced':gap,'claim_boundary':'Reproduces a v0.41 temporal-history limitation when a deterministic bond identity is revoked and later reused; current-state integrity can still pass while an earlier interval is no longer reconstructable.'}
(OUT/'TEMPORAL_CYCLE_REGRESSION_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
print('TEMPORAL_CYCLE_GAP_REPRODUCED='+str(gap),flush=True)
print('INTEGRITY_PASS='+str(verify['pass']),flush=True)
print('EXPECTED_INITIAL='+json.dumps(expected,sort_keys=True),flush=True)
print('ACTUAL_AT_INITIAL_SEQ='+json.dumps(actual,sort_keys=True),flush=True)
print('DIFFERENCES='+json.dumps(diff,sort_keys=True),flush=True)
print('CLAIM_BOUNDARY=known v0.41 interval-history limitation under repeated bond identity; not a current-state integrity failure',flush=True)
