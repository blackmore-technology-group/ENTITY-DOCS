from pathlib import Path
import sys, json, shutil, hashlib, time, statistics
SITE=Path(r'E:\ENTITY_ACTIVE\ENTITY_TESTING_20261001\qualification_site_v343')
sys.path.insert(0,str(SITE))
import numpy as np
OUT=Path(r'E:\ENTITY_ACTIVE\ENTITY_STORAGE_SCENARIOS_20261001\fanout_curve')
BONDS=25_000_000
FANOUTS=[1,2,5,10,20]
CHUNK=2_500_000
DT=np.dtype([('source','<u4'),('predicate','<u2'),('flags','<u2'),('target','<u8')],align=False)
REC=DT.itemsize
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True)
rows=[]; all_pass=True
for fanout in FANOUTS:
    entities=BONDS//fanout
    wr=OUT/f'fanout_{fanout}'; wr.mkdir(parents=True)
    bp=wr/'bonds.bin'; ip=wr/'entity_index.u64'
    bh=hashlib.sha256(); ih=hashlib.sha256()
    with open(bp,'wb',buffering=8*1024*1024) as f:
        for start in range(0,BONDS,CHUNK):
            n=min(CHUNK,BONDS-start); ids=np.arange(start,start+n,dtype=np.uint64); a=np.empty(n,dtype=DT)
            a['source']=(ids//fanout).astype(np.uint32); a['predicate']=(ids%37).astype(np.uint16); a['flags']=1
            a['target']=ids*np.uint64(6364136223846793005)+np.uint64(1442695040888963407)
            bh.update(a); a.tofile(f)
    with open(ip,'wb',buffering=8*1024*1024) as f:
        for start in range(0,entities,CHUNK):
            n=min(CHUNK,entities-start); off=np.arange(start,start+n,dtype=np.uint64)*np.uint64(fanout*REC); ih.update(off); off.tofile(f)
    bm=np.memmap(bp,dtype=DT,mode='r'); im=np.memmap(ip,dtype='<u8',mode='r'); rng=np.random.default_rng(342+fanout)
    lat=[]; ok=True
    for s in rng.integers(0,entities,size=500,dtype=np.int64):
        q=time.perf_counter_ns(); rec0=int(im[int(s)])//REC; part=bm[rec0:rec0+fanout]; _=int(part['target'][0]); lat.append((time.perf_counter_ns()-q)/1000)
        ok=ok and len(part)==fanout and bool(np.all(part['source']==s))
    bond_bytes=bp.stat().st_size; index_bytes=ip.stat().st_size; total=bond_bytes+index_bytes
    vector=entities*768*4; reduction=100.0*(vector-total)/vector
    row={'fanout':fanout,'bonds':BONDS,'entities':entities,'bond_bytes':bond_bytes,'index_bytes':index_bytes,'total_bytes':total,'index_share_percent':100.0*index_bytes/total,'vector_768d_float32_bytes':vector,'reduction_vs_768d_vector_percent':reduction,'lookup_samples':500,'lookup_correct':ok,'median_lookup_us':statistics.median(lat),'p95_lookup_us':float(np.percentile(lat,95)),'bond_sha256':bh.hexdigest(),'index_sha256':ih.hexdigest(),'pass':bool(ok and bond_bytes==BONDS*REC and index_bytes==entities*8)}
    rows.append(row); all_pass=all_pass and row['pass']
    print(f"FANOUT={fanout} ENTITIES={entities} TOTAL_BYTES={total} INDEX_SHARE={row['index_share_percent']:.4f}% VECTOR_BASELINE={vector} REDUCTION={reduction:.6f}% LOOKUPS=500/500 PASS={row['pass']}",flush=True)
result={'scenario':'storage-fanout-density-curve','bonds':BONDS,'rows':rows,'pass':all_pass,'claim_boundary':'Fixed-bond synthetic compact representation measuring actual bond/index bytes as entity fanout changes; vector comparison uses one 768-d float32 vector per entity and is not a universal workload model.'}
(OUT/'FANOUT_CURVE_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
print('FANOUT_CURVE_PASS='+str(all_pass),flush=True)
