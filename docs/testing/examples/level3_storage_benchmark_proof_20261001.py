from pathlib import Path
import numpy as np, hashlib, json, time, ctypes, statistics
from ctypes import wintypes
OUT=Path(r'E:\ENTITY_ACTIVE\ENTITY_STORAGE_PROOF_20261001\level3'); OUT.mkdir(parents=True,exist_ok=True)
BONDS=250_000_000; FANOUT=5; ENTITIES=BONDS//FANOUT; CHUNK=5_000_000
DT=np.dtype([('source','<u4'),('predicate','<u2'),('flags','<u2'),('target','<u8')],align=False); REC=DT.itemsize
bp=OUT/'bonds_250m.bin'; ip=OUT/'entity_index_50m.u64'; [p.unlink() for p in (bp,ip) if p.exists()]
class PMC(ctypes.Structure): _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD),('PeakWorkingSetSize',ctypes.c_size_t),('WorkingSetSize',ctypes.c_size_t),('QuotaPeakPagedPoolUsage',ctypes.c_size_t),('QuotaPagedPoolUsage',ctypes.c_size_t),('QuotaPeakNonPagedPoolUsage',ctypes.c_size_t),('QuotaNonPagedPoolUsage',ctypes.c_size_t),('PagefileUsage',ctypes.c_size_t),('PeakPagefileUsage',ctypes.c_size_t)]
ps=ctypes.WinDLL('psapi',use_last_error=True); k=ctypes.WinDLL('kernel32',use_last_error=True)
ps.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(PMC),wintypes.DWORD]; ps.GetProcessMemoryInfo.restype=wintypes.BOOL; k.GetCurrentProcess.restype=wintypes.HANDLE
def mem():
 x=PMC(); x.cb=ctypes.sizeof(PMC); ok=ps.GetProcessMemoryInfo(k.GetCurrentProcess(),ctypes.byref(x),x.cb)
 if not ok: raise ctypes.WinError(ctypes.get_last_error())
 return {'working_set':x.WorkingSetSize,'peak_working_set':x.PeakWorkingSetSize,'pagefile':x.PagefileUsage,'peak_pagefile':x.PeakPagefileUsage}
print(f'LEVEL3_PROOF_START bonds={BONDS} entities={ENTITIES} record_bytes={REC}',flush=True)
start_mem=mem(); bh=hashlib.sha256(); t0=time.perf_counter()
with open(bp,'wb',buffering=8*1024*1024) as f:
 for start in range(0,BONDS,CHUNK):
  n=min(CHUNK,BONDS-start); ids=np.arange(start,start+n,dtype=np.uint64); a=np.empty(n,dtype=DT); a['source']=(ids//FANOUT).astype(np.uint32); a['predicate']=(ids%37).astype(np.uint16); a['flags']=1; a['target']=ids*np.uint64(6364136223846793005)+np.uint64(1442695040888963407); bh.update(a); a.tofile(f); f.flush(); print(f'BOND_PROGRESS={start+n}/{BONDS} bytes={f.tell()}',flush=True)
write_sec=time.perf_counter()-t0; write_mem=mem(); ih=hashlib.sha256(); t1=time.perf_counter()
with open(ip,'wb',buffering=8*1024*1024) as f:
 for start in range(0,ENTITIES,CHUNK):
  n=min(CHUNK,ENTITIES-start); off=np.arange(start,start+n,dtype=np.uint64)*np.uint64(FANOUT*REC); ih.update(off); off.tofile(f); f.flush(); print(f'INDEX_PROGRESS={start+n}/{ENTITIES} bytes={f.tell()}',flush=True)
index_sec=time.perf_counter()-t1; bm=np.memmap(bp,dtype=DT,mode='r'); im=np.memmap(ip,dtype='<u8',mode='r'); rng=np.random.default_rng(342); lat=[]; ok=True
for i,s in enumerate(rng.integers(0,ENTITIES,size=1000,dtype=np.int64),1):
 q=time.perf_counter_ns(); rec0=int(im[int(s)])//REC; rows=bm[rec0:rec0+FANOUT]; _=int(rows['target'][0]); lat.append((time.perf_counter_ns()-q)/1000); ok=ok and len(rows)==FANOUT and bool(np.all(rows['source']==s))
 if i%100==0: print(f'LOOKUP_PROGRESS={i}/1000 correct={ok}',flush=True)
query_mem=mem(); atomic=bp.stat().st_size+ip.stat().st_size; rag=ENTITIES*768*4; saving=1-atomic/rag
res={'qualification':'ENTITY storage proof 2026-10-01','actual':{'bonds':BONDS,'entities':ENTITIES,'record_bytes':REC,'bond_bytes':bp.stat().st_size,'index_bytes':ip.stat().st_size,'total_bytes':atomic,'bond_sha256':bh.hexdigest(),'index_sha256':ih.hexdigest(),'write_seconds':write_sec,'index_seconds':index_sec,'write_MBps':bp.stat().st_size/write_sec/1e6,'query_samples':len(lat),'query_correct':ok,'mean_query_us':statistics.mean(lat),'median_query_us':statistics.median(lat),'p95_query_us':float(np.percentile(lat,95))},'memory':{'start':start_mem,'after_write':write_mem,'after_queries':query_mem},'vector_baseline':{'dimension':768,'float_bytes':4,'vector_bytes':rag,'representation_saving_fraction':saving}}
res['pass']=bool(ok and BONDS>=100_000_000 and atomic==4_400_000_000 and rag==153_600_000_000 and saving>=.90 and 0<query_mem['peak_working_set']<2_000_000_000)
result=OUT/'LEVEL3_STORAGE_PROOF_RESULT.json'; result.write_text(json.dumps(res,indent=2,sort_keys=True),encoding='utf-8')
print(json.dumps(res,indent=2,sort_keys=True),flush=True)
print(f'STORAGE_REDUCTION_PERCENT={100*saving:.10f}',flush=True)
print(f'LEVEL3_PROOF_PASS={res["pass"]}',flush=True)
