from pathlib import Path
import sys, json, gzip, lzma, sqlite3, random, shutil, time, statistics
ROOT=Path(r'E:\ENTITY_ACTIVE\BTG_BUILT_LOCALAPPDATA\BTG\ADAM_RC2\ADAM_v1_0_COMPLETE_SOFTWARE_REFERENCE_RC2')
sys.path.insert(0,str(ROOT))
from adam_v41.audit import _dataset, _sqlite_baseline
from adam_v41.canonical import canonical_json_bytes
from adam_v41.universe import AtomicUniverse
from adam_v41.brain import AtomicBrain
OUT=Path(r'E:\ENTITY_ACTIVE\ENTITY_STORAGE_SCENARIOS_20261001\archive_live_store_tradeoff')
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True)
rows=_dataset('mixed',5000,20261001)
corpus=b'\n'.join(canonical_json_bytes(r) for r in rows)+b'\n'
gz=gzip.compress(corpus,compresslevel=9); xz=lzma.compress(corpus,preset=9)
sqlite_path=OUT/'baseline.sqlite'; _sqlite_baseline(sqlite_path,rows)
u=AtomicUniverse(OUT/'adam'); brain=AtomicBrain(u)
ids=brain.ingest_records(rows,entity_type='project',id_field='project_id')
rng=random.Random(20261001); indices=[rng.randrange(len(rows)) for _ in range(100)]
def stats(us):
    s=sorted(us); return {'median_us':statistics.median(s),'p95_us':s[int(len(s)*.95)-1],'mean_us':statistics.mean(s)}
con=sqlite3.connect(sqlite_path)
sql_us=[]; adam_us=[]; gz_us=[]; xz_us=[]
for i in indices:
    key=rows[i]['project_id']
    t=time.perf_counter_ns(); rec=con.execute('SELECT project_id,location,status,crew,budget,cost,note FROM projects WHERE project_id=?',(key,)).fetchone(); sql_us.append((time.perf_counter_ns()-t)/1000)
    assert rec and rec[0]==key
    t=time.perf_counter_ns(); v=u.entity_view(ids[i]); adam_us.append((time.perf_counter_ns()-t)/1000); assert v['_key']==key
    t=time.perf_counter_ns(); line=gzip.decompress(gz).splitlines()[i]; obj=json.loads(line); gz_us.append((time.perf_counter_ns()-t)/1000); assert obj['project_id']==key
    t=time.perf_counter_ns(); line=lzma.decompress(xz).splitlines()[i]; obj=json.loads(line); xz_us.append((time.perf_counter_ns()-t)/1000); assert obj['project_id']==key
con.close()
idx=2500; changed=dict(rows[idx]); changed['note']='updated-one-record-for-live-store-tradeoff'
new_lines=corpus.splitlines(); new_lines[idx]=canonical_json_bytes(changed); new_corpus=b'\n'.join(new_lines)+b'\n'
t=time.perf_counter_ns(); gz2=gzip.compress(new_corpus,compresslevel=9); gz_update_us=(time.perf_counter_ns()-t)/1000
t=time.perf_counter_ns(); xz2=lzma.compress(new_corpus,preset=9); xz_update_us=(time.perf_counter_ns()-t)/1000
journal=OUT/'adam'/'universe.a41log'; before=journal.stat().st_size
facts={k:v for k,v in changed.items() if k!='project_id'}; version=u.entity_versions[ids[idx]]
t=time.perf_counter_ns(); u.assert_entity('project',changed['project_id'],facts,expected_version=version); adam_update_us=(time.perf_counter_ns()-t)/1000
after=journal.stat().st_size; adam_append_bytes=after-before
reopened=AtomicUniverse(OUT/'adam'); latest=reopened.entity_view(ids[idx]); update_ok=(latest['note']==changed['note'] and reopened.verify()['pass'])
result={'scenario':'archive-vs-live-store-tradeoff','pass':update_ok,'dataset':'mixed-5000','bytes':{'canonical_ndjson':len(corpus),'gzip9':len(gz),'xz_lzma9':len(xz),'sqlite':sqlite_path.stat().st_size,'adam_factored':len(u.native_factored_state_bytes())},'lookup_100':{'sqlite':stats(sql_us),'adam_entity_view':stats(adam_us),'gzip_full_decompress_then_line':stats(gz_us),'xz_full_decompress_then_line':stats(xz_us)},'single_record_update':{'gzip_recompressed_archive_bytes':len(gz2),'gzip_recompress_us':gz_update_us,'xz_recompressed_archive_bytes':len(xz2),'xz_recompress_us':xz_update_us,'adam_journal_append_bytes':adam_append_bytes,'adam_update_us':adam_update_us,'adam_restart_verified':update_ok},'claim_boundary':'Single-machine sequential microbenchmark on one 5,000-record mixed dataset. Compressed-archive lookup intentionally models whole-archive decompression without a separate index; other compressed/indexed formats may behave differently. Timings are illustrative, not production performance claims.'}
(OUT/'ARCHIVE_LIVE_STORE_TRADEOFF_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
print(f"LOOKUP_MEDIAN_US sqlite={result['lookup_100']['sqlite']['median_us']:.1f} adam={result['lookup_100']['adam_entity_view']['median_us']:.1f} gzip={result['lookup_100']['gzip_full_decompress_then_line']['median_us']:.1f} xz={result['lookup_100']['xz_full_decompress_then_line']['median_us']:.1f}",flush=True)
print(f"UPDATE gzip_archive_bytes={len(gz2)} xz_archive_bytes={len(xz2)} adam_journal_append_bytes={adam_append_bytes} restart={update_ok}",flush=True)
print('ARCHIVE_LIVE_STORE_TRADEOFF_PASS='+str(result['pass']),flush=True)
