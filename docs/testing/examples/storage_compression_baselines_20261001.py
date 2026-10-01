from pathlib import Path
import sys, json, gzip, bz2, lzma, shutil
ROOT=Path(r'E:\ENTITY_ACTIVE\BTG_BUILT_LOCALAPPDATA\BTG\ADAM_RC2\ADAM_v1_0_COMPLETE_SOFTWARE_REFERENCE_RC2')
sys.path.insert(0,str(ROOT))
from adam_v41.audit import _dataset, _sqlite_baseline
from adam_v41.canonical import canonical_json_bytes
from adam_v41.universe import AtomicUniverse
from adam_v41.brain import AtomicBrain
OUT=Path(r'E:\ENTITY_ACTIVE\ENTITY_STORAGE_SCENARIOS_20261001\compression_baselines')
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True)
rows_out=[]; seed=20261001
for off,mode in enumerate(('repetitive','mixed','unique')):
    rows=_dataset(mode,5000,seed+off)
    corpus=b'\n'.join(canonical_json_bytes(r) for r in rows)+b'\n'
    wr=OUT/mode; wr.mkdir()
    sqlite_bytes=_sqlite_baseline(wr/'baseline.sqlite',rows)
    u=AtomicUniverse(wr/'adam'); brain=AtomicBrain(u)
    ids=brain.ingest_records(rows,entity_type='project',id_field='project_id')
    factored=len(u.native_factored_state_bytes()); packed=len(u.native_packed_state_bytes())
    gz=gzip.compress(corpus,compresslevel=9)
    bz=bz2.compress(corpus,compresslevel=9)
    xz=lzma.compress(corpus,preset=9)
    views_equal=all({k:v for k,v in u.entity_view(eid).items() if not k.startswith('_')} == {k:v for k,v in row.items() if k!='project_id'} for eid,row in zip(ids,rows))
    restart=AtomicUniverse(wr/'adam')
    restart_ok=restart.verify()['pass'] and restart.entity_view(ids[-1])==u.entity_view(ids[-1])
    pass_row=(gzip.decompress(gz)==corpus and bz2.decompress(bz)==corpus and lzma.decompress(xz)==corpus and views_equal and restart_ok)
    row={'mode':mode,'records':5000,'canonical_ndjson_bytes':len(corpus),'sqlite_bytes':sqlite_bytes,'gzip9_bytes':len(gz),'bzip2_9_bytes':len(bz),'xz_lzma9_bytes':len(xz),'adam_factored_bytes':factored,'adam_packed_bytes':packed,'exact_views':views_equal,'restart_recovery':restart_ok,'pass':pass_row}
    row['adam_factored_vs_sqlite_reduction_percent']=100*(sqlite_bytes-factored)/sqlite_bytes
    row['adam_factored_vs_gzip_reduction_percent']=100*(len(gz)-factored)/len(gz)
    row['adam_factored_vs_bzip2_reduction_percent']=100*(len(bz)-factored)/len(bz)
    row['adam_factored_vs_xz_reduction_percent']=100*(len(xz)-factored)/len(xz)
    rows_out.append(row)
    print(f"COMPRESSION mode={mode} raw={len(corpus)} sqlite={sqlite_bytes} gzip={len(gz)} bzip2={len(bz)} xz={len(xz)} factored={factored} pass={pass_row}",flush=True)
result={'scenario':'storage-conventional-compression-baselines','pass':all(r['pass'] for r in rows_out),'rows':rows_out,'claim_boundary':'Compares physical byte counts for the same generated 5,000-record datasets. gzip/bzip2/XZ are compressed canonical NDJSON blobs, while SQLite and ADAM are structured stores with different query/history semantics; byte comparisons do not imply feature equivalence.'}
(OUT/'COMPRESSION_BASELINES_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
print('COMPRESSION_BASELINES_PASS='+str(result['pass']),flush=True)
