from pathlib import Path
import sys, json, shutil
INSTALLED=Path(r'E:\ENTITY_ACTIVE\BTG_BUILT_LOCALAPPDATA\BTG\ADAM_RC2\ADAM_v1_0_COMPLETE_SOFTWARE_REFERENCE_RC2')
OUT=Path(r'E:\ENTITY_ACTIVE\ENTITY_STORAGE_SCENARIOS_20261001\history_unique_curve')
sys.path.insert(0,str(INSTALLED))
from adam_v41.audit import _sqlite_baseline, _size_tree
from adam_v41.brain import AtomicBrain
from adam_v41.universe import AtomicUniverse
N=200
DEPTHS=[0,1,3,10,25]
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True)
rows_out=[]; all_pass=True

def base_rows():
    return [{'project_id':f'P-{i:07d}','location':['Grand Forks','Christina Lake','Boundary'][i%3],'status':'active','crew':f'crew-{i%8}','budget':100000+(i%50)*1000,'cost':95000+(i%50)*1000,'note':'initial'} for i in range(N)]
for depth in DEPTHS:
    wr=OUT/f'updates_{depth}'
    initial=base_rows()
    u=AtomicUniverse(wr/'adam'); brain=AtomicBrain(u)
    ids=brain.ingest_records(initial,entity_type='project',id_field='project_id')
    initial_seq=u.sequence; initial_first=u.entity_view(ids[0])
    final=[dict(r) for r in initial]
    for step in range(1,depth+1):
        for i,(eid,row) in enumerate(zip(ids,final)):
            row['cost']=95000+(i%50)*1000+step*100
            row['status']=f'state-{step:03d}'
            row['note']=f'update-{step:03d}'
            fields={k:v for k,v in row.items() if k!='project_id'}
            u.assert_entity('project',row['project_id'],fields,expected_version=u.entity_versions[eid])
    sqlite_bytes=_sqlite_baseline(wr/'final.sqlite',final)
    verify=u.verify(); factored=len(u.native_factored_state_bytes()); packed=len(u.native_packed_state_bytes())
    journal=(wr/'adam'/'universe.a41log').stat().st_size
    time_travel=(u.entity_view(ids[0],at_seq=initial_seq)==initial_first)
    latest_exact=all({k:v for k,v in u.entity_view(eid).items() if not k.startswith('_')}=={k:v for k,v in row.items() if k!='project_id'} for eid,row in zip(ids[:25],final[:25]))
    root=u.root_hash; last=u.entity_view(ids[-1]); u.compact_authority(); del u
    reopened=AtomicUniverse(wr/'adam'); restart=(reopened.root_hash==root and reopened.entity_view(ids[-1])==last and reopened.verify()['pass'])
    tree=_size_tree(wr/'adam'); factored_reduction=100.0*(sqlite_bytes-factored)/sqlite_bytes; journal_ratio=journal/sqlite_bytes
    row={'entities':N,'updates_per_entity':depth,'sqlite_current_bytes':sqlite_bytes,'factored_current_bytes':factored,'packed_current_bytes':packed,'journal_bytes':journal,'compacted_tree_bytes':tree,'factored_vs_sqlite_reduction_percent':factored_reduction,'journal_to_sqlite_ratio':journal_ratio,'time_travel_initial_state':time_travel,'latest_exact':latest_exact,'restart_recovery':restart,'integrity':verify['pass']}
    row['pass']=bool(time_travel and latest_exact and restart and verify['pass'])
    rows_out.append(row); all_pass=all_pass and row['pass']
    print(f"HISTORY_UNIQUE updates={depth} sqlite_current={sqlite_bytes} factored_current={factored} factored_reduction={factored_reduction:.6f}% journal={journal} journal_x_sqlite={journal_ratio:.3f} time_travel={time_travel} pass={row['pass']}",flush=True)
result={'scenario':'storage-history-provenance-cost-unique-updates','entities':N,'rows':rows_out,'pass':all_pass,'claim_boundary':'Uses monotonic unique update values so deterministic bond IDs are not revisited. Measures retained history cost versus a SQLite current-state-only baseline; not universal temporal storage efficiency.'}
(OUT/'HISTORY_UNIQUE_CURVE_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
print('HISTORY_UNIQUE_CURVE_PASS='+str(all_pass),flush=True)
