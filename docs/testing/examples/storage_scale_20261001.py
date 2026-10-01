from pathlib import Path
import sys, json, shutil, random
INSTALLED=Path(r'E:\ENTITY_ACTIVE\BTG_BUILT_LOCALAPPDATA\BTG\ADAM_RC2\ADAM_v1_0_COMPLETE_SOFTWARE_REFERENCE_RC2')
OUT=Path(r'E:\ENTITY_ACTIVE\ENTITY_STORAGE_SCENARIOS_20261001\scale_curve')
sys.path.insert(0,str(INSTALLED))
from adam_v41.audit import _dataset, _sqlite_baseline, _size_tree
from adam_v41.brain import AtomicBrain
from adam_v41.universe import AtomicUniverse
SIZES=[100,500,1500,5000]
MODES=['repetitive','mixed','unique']
SEED=20261001
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True)
rows_out=[]
all_pass=True
for n in SIZES:
    for mi,mode in enumerate(MODES):
        wr=OUT/f'{mode}_{n}'
        wr.mkdir(parents=True,exist_ok=True)
        data=_dataset(mode,n,SEED+n+mi)
        sqlite_bytes=_sqlite_baseline(wr/'baseline.sqlite',data)
        u=AtomicUniverse(wr/'adam'); brain=AtomicBrain(u)
        ids=brain.ingest_records(data,entity_type='project',id_field='project_id')
        verify=u.verify(); factored=len(u.native_factored_state_bytes()); packed=len(u.native_packed_state_bytes())
        journal=(wr/'adam'/'universe.a41log').stat().st_size
        exact=True
        for idx in random.Random(SEED+n).sample(range(n),min(25,n)):
            view={k:v for k,v in u.entity_view(ids[idx]).items() if not k.startswith('_')}
            expected={k:v for k,v in data[idx].items() if k!='project_id'}
            exact=exact and view==expected
        root=u.root_hash; last=u.entity_view(ids[-1]); u.compact_authority(); del u
        reopened=AtomicUniverse(wr/'adam'); restart=(reopened.root_hash==root and reopened.entity_view(ids[-1])==last and reopened.verify()['pass'])
        tree=_size_tree(wr/'adam')
        reduction=100.0*(sqlite_bytes-factored)/sqlite_bytes
        row={'mode':mode,'records':n,'sqlite_bytes':sqlite_bytes,'factored_bytes':factored,'packed_bytes':packed,'journal_bytes':journal,'compacted_tree_bytes':tree,'factored_vs_sqlite_reduction_percent':reduction,'exact_views':exact,'restart_recovery':restart,'integrity':verify['pass'],'atoms':verify['atoms'],'bonds':verify['bonds'],'compounds':verify['compounds']}
        row['pass']=bool(exact and restart and verify['pass'])
        rows_out.append(row); all_pass=all_pass and row['pass']
        print(f"SCALE mode={mode} records={n} sqlite={sqlite_bytes} factored={factored} reduction={reduction:.6f}% journal={journal} compacted={tree} pass={row['pass']}",flush=True)
result={'scenario':'storage-scale-curve','sizes':SIZES,'modes':MODES,'rows':rows_out,'pass':all_pass,'claim_boundary':'Measured single-node ADAM v0.41 current-state factoring versus vacuumed SQLite for these generated workloads; not universal database compression.'}
(OUT/'SCALE_CURVE_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
print('SCALE_CURVE_PASS='+str(all_pass),flush=True)
