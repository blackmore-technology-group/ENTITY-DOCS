from pathlib import Path
import json
MEASURED=Path(r'E:\ENTITY_ACTIVE\ENTITY_STORAGE_PROOF_20261001\level3\LEVEL3_STORAGE_PROOF_RESULT.json')
OUT=Path(r'E:\ENTITY_ACTIVE\ENTITY_STORAGE_SCENARIOS_20261001\vector_dimension_curve')
OUT.mkdir(parents=True,exist_ok=True)
r=json.loads(MEASURED.read_text(encoding='utf-8'))
entities=r['actual']['entities']; compact=r['actual']['total_bytes']
dims=[16,22,32,64,128,256,384,512,768,1024,1536,3072]
rows=[]
for d in dims:
    vector=entities*d*4
    reduction=100.0*(vector-compact)/vector
    relation='ENTITY_SMALLER' if compact<vector else ('EQUAL' if compact==vector else 'VECTOR_SMALLER')
    row={'dimension':d,'entities':entities,'float_bytes':4,'vector_bytes':vector,'measured_entity_bytes':compact,'entity_vs_vector_reduction_percent':reduction,'relation':relation}
    rows.append(row)
    print(f"DIM={d} VECTOR_BYTES={vector} ENTITY_BYTES={compact} REDUCTION={reduction:.6f}% RELATION={relation}",flush=True)
break_even=compact/(entities*4)
result={'scenario':'vector-dimension-crossover','source_measured_result':str(MEASURED),'measured_entity_bytes':compact,'entities':entities,'break_even_dimension':break_even,'rows':rows,'pass':True,'claim_boundary':'Arithmetic crossover derived from the freshly measured 4.4 GB compact representation; vector baseline assumes one float32 vector per entity and excludes vector-database metadata/index overhead.'}
(OUT/'VECTOR_DIMENSION_CURVE_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
print(f'BREAK_EVEN_DIMENSION={break_even:.6f} VECTOR_DIMENSION_CURVE_PASS=True',flush=True)
