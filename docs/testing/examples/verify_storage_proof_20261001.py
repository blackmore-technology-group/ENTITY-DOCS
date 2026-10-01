from pathlib import Path
import hashlib, json
ROOT=Path(r'E:\ENTITY_ACTIVE\ENTITY_STORAGE_PROOF_20261001')
HIST=Path(r'E:\ADAM_ATOMIC_UNIVERSE_PROOF\LEVEL23_QUALIFICATION\level3_scale_corrected\LEVEL3_SCALE_CORRECTED_RESULT.json')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
 return h.hexdigest()
r=json.loads((ROOT/'level3/LEVEL3_STORAGE_PROOF_RESULT.json').read_text())
h=json.loads(HIST.read_text())
bp=ROOT/'level3/bonds_250m.bin'; ip=ROOT/'level3/entity_index_50m.u64'
bh=sha(bp); ih=sha(ip)
checks={'bond_bytes':bp.stat().st_size==4_000_000_000,'index_bytes':ip.stat().st_size==400_000_000,'bond_hash_result':bh==r['actual']['bond_sha256'],'index_hash_result':ih==r['actual']['index_sha256'],'bond_hash_historical':bh==h['actual']['bond_sha256'],'index_hash_historical':ih==h['actual']['index_sha256'],'query_correct':r['actual']['query_correct'] and r['actual']['query_samples']==1000,'reduction_exact':abs(r['vector_baseline']['representation_saving_fraction']-0.9713541666666666)<1e-15,'result_pass':r['pass'] is True}
for k,v in checks.items(): print(f'{k.upper()}={"PASS" if v else "FAIL"}')
print(f'BOND_SHA256={bh}'); print(f'INDEX_SHA256={ih}')
print(f'REDUCTION_PERCENT={100*r["vector_baseline"]["representation_saving_fraction"]:.10f}')
print('CLAIM_BOUNDARY=controlled compact bond+index representation versus 768-d float32 vector baseline; not universal compression')
print('STORAGE_PROOF_VERIFICATION=PASS' if all(checks.values()) else 'STORAGE_PROOF_VERIFICATION=FAIL')
raise SystemExit(0 if all(checks.values()) else 1)
