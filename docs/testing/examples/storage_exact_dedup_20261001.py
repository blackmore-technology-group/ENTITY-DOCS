from pathlib import Path
import sys, json, random, shutil
ROOT=Path(r'E:\ENTITY_ACTIVE\BTG_BUILT_LOCALAPPDATA\BTG\ADAM_RC2\ADAM_v1_0_COMPLETE_SOFTWARE_REFERENCE_RC2')
sys.path.insert(0,str(ROOT))
from adam_v41.universe import AtomicUniverse
from adam_v41.exact import ExactCodec
OUT=Path(r'E:\ENTITY_ACTIVE\ENTITY_STORAGE_SCENARIOS_20261001\exact_dedup_curve')
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True)
OBJECTS=64; SIZE=128*1024; ratios=(0,25,50,75,90,98)
rows=[]
for ratio in ratios:
    wr=OUT/f'dup_{ratio}'; wr.mkdir()
    unique=max(1,round(OBJECTS*(100-ratio)/100))
    rng=random.Random(20261001+ratio)
    payloads=[rng.randbytes(SIZE) for _ in range(unique)]
    u=AtomicUniverse(wr/'adam'); codec=ExactCodec(u); objects=[]
    for i in range(OBJECTS):
        data=payloads[i%unique]
        objects.append((codec.ingest(data,name=f'object-{i:03d}.bin'),data))
    raw_bytes=OBJECTS*SIZE
    chunk_payload_bytes=sum(len(a.value) for a in u.atoms.values() if a.kind=='exact_chunk')
    packed_bytes=len(u.native_packed_state_bytes())
    journal_bytes=(wr/'adam'/'universe.a41log').stat().st_size
    exact_now=all(codec.reconstruct(obj.object_id)==data for obj,data in objects)
    reopened=AtomicUniverse(wr/'adam'); recodec=ExactCodec(reopened)
    exact_restart=all(recodec.reconstruct(obj.object_id)==data for obj,data in objects[::8])
    verify=reopened.verify()['pass']
    row={'duplicate_target_percent':ratio,'objects':OBJECTS,'payload_bytes_each':SIZE,'unique_payloads':unique,'raw_corpus_bytes':raw_bytes,'unique_chunk_payload_bytes':chunk_payload_bytes,'packed_state_bytes':packed_bytes,'journal_bytes':journal_bytes,'exact_reconstruction':exact_now,'restart_sample_reconstruction':exact_restart,'integrity':verify}
    row['chunk_payload_reduction_percent']=100*(raw_bytes-chunk_payload_bytes)/raw_bytes
    row['packed_state_vs_raw_reduction_percent']=100*(raw_bytes-packed_bytes)/raw_bytes
    row['pass']=exact_now and exact_restart and verify
    rows.append(row)
    print(f"DEDUP target={ratio}% unique={unique} raw={raw_bytes} chunks={chunk_payload_bytes} chunk_reduction={row['chunk_payload_reduction_percent']:.3f}% packed={packed_bytes} packed_reduction={row['packed_state_vs_raw_reduction_percent']:.3f}% journal={journal_bytes} pass={row['pass']}",flush=True)
result={'scenario':'exact-content-addressed-dedup-curve','pass':all(r['pass'] for r in rows),'rows':rows,'claim_boundary':'Measures exact-content chunk reuse for 64 synthetic 128 KiB objects with repeated whole-object payloads. unique_chunk_payload_bytes isolates payload deduplication; packed state and journal include object recipes/metadata/history overhead. This is not a universal file-compression result.'}
(OUT/'EXACT_DEDUP_CURVE_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
print('EXACT_DEDUP_CURVE_PASS='+str(result['pass']),flush=True)
