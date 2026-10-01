from pathlib import Path
import sys, json, shutil, random
INSTALLED=Path(r'E:\ENTITY_ACTIVE\BTG_BUILT_LOCALAPPDATA\BTG\ADAM_RC2\ADAM_v1_0_COMPLETE_SOFTWARE_REFERENCE_RC2')
OUT=Path(r'E:\ENTITY_ACTIVE\ENTITY_STORAGE_SCENARIOS_20261001\cardinality_curve')
sys.path.insert(0,str(INSTALLED))
from adam_v41.audit import _sqlite_baseline, _size_tree
from adam_v41.brain import AtomicBrain
from adam_v41.universe import AtomicUniverse
N=3000
CARDINALITIES=[1,3,10,30,100,300,1000,3000]
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True)
rows_out=[]; all_pass=True

def dataset(card):
    rows=[]
    for i in range(N):
        rows.append({'project_id':f'P-{i:07d}','location':f'loc-{i%card:05d}','status':f'state-{i%min(card,50):03d}','crew':f'crew-{i%min(card,500):04d}','budget':100000+(i%50)*1000,'cost':95000+(i%50)*1000,'note':f'note-{i%card:05d}'})
    return rows
for card in CARDINALITIES:
    wr=OUT/f'card_{card}'
    wr.mkdir(parents=True,exist_ok=True)
    data=dataset(card)
    sqlite_bytes=_sqlite_baseline(wr/'baseline.sqlite',data)
    u=AtomicUniverse(wr/'adam'); brain=AtomicBrain(u)
    ids=brain.ingest_records(data,entity_type='project',id_field='project_id')
    verify=u.verify(); factored=len(u.native_factored_state_bytes()); packed=len(u.native_packed_state_bytes())
    journal=(wr/'adam'/'universe.a41log').stat().st_size
    exact=True
    for idx in random.Random(342+card).sample(range(N),25):
        view={k:v for k,v in u.entity_view(ids[idx]).items() if not k.startswith('_')}
        expected={k:v for k,v in data[idx].items() if k!='project_id'}
        exact=exact and view==expected
    root=u.root_hash; last=u.entity_view(ids[-1]); u.compact_authority(); del u
    reopened=AtomicUniverse(wr/'adam'); restart=(reopened.root_hash==root and reopened.entity_view(ids[-1])==last and reopened.verify()['pass'])
    tree=_size_tree(wr/'adam'); reduction=100.0*(sqlite_bytes-factored)/sqlite_bytes
    row={'records':N,'value_cardinality':card,'sqlite_bytes':sqlite_bytes,'factored_bytes':factored,'packed_bytes':packed,'journal_bytes':journal,'compacted_tree_bytes':tree,'factored_vs_sqlite_reduction_percent':reduction,'exact_views':exact,'restart_recovery':restart,'integrity':verify['pass'],'atoms':verify['atoms'],'bonds':verify['bonds'],'compounds':verify['compounds']}
    row['pass']=bool(exact and restart and verify['pass'])
    rows_out.append(row); all_pass=all_pass and row['pass']
    print(f"CARDINALITY values={card} records={N} sqlite={sqlite_bytes} factored={factored} reduction={reduction:.6f}% journal={journal} pass={row['pass']}",flush=True)
break_even=next((r['value_cardinality'] for r in rows_out if r['factored_vs_sqlite_reduction_percent']<=0),None)
result={'scenario':'storage-cardinality-break-even','records':N,'rows':rows_out,'first_non_saving_cardinality':break_even,'pass':all_pass,'claim_boundary':'Measures value reuse/cardinality sensitivity for one fixed synthetic project schema; break-even is workload-specific.'}
(OUT/'CARDINALITY_CURVE_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
print(f'CARDINALITY_CURVE_PASS={all_pass} FIRST_NON_SAVING_CARDINALITY={break_even}',flush=True)
