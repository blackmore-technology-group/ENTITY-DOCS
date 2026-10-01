from pathlib import Path
import json

FRESH=Path(r"E:\ENTITY_ACTIVE\ENTITY_TESTING_20261001\runs\level3-storage\LEVEL3_SCALE_CORRECTED_RESULT.json")
HISTORICAL=Path(r"E:\ADAM_ATOMIC_UNIVERSE_PROOF\LEVEL23_QUALIFICATION\level3_scale_corrected\LEVEL3_SCALE_CORRECTED_RESULT.json")
fresh=json.loads(FRESH.read_text(encoding="utf-8"))
hist=json.loads(HISTORICAL.read_text(encoding="utf-8"))
a=fresh["actual"]; h=hist["actual"]; r=fresh["rag_baseline"]
assert fresh["pass"] is True and a["query_correct"] is True and a["query_samples"] == 1000
assert a["bonds"] == 250_000_000 and a["entities"] == 50_000_000
assert a["total_bytes"] == 4_400_000_000 and r["vector_bytes"] == 153_600_000_000
assert a["bond_sha256"] == h["bond_sha256"]
assert a["index_sha256"] == h["index_sha256"]
assert abs(r["atomic_vs_vectors_saving_fraction"] - 0.9713541666666666) < 1e-15
print("STORAGE_REQUALIFICATION=PASS")
print(f"BONDS={a['bonds']}")
print(f"ENTITIES={a['entities']}")
print(f"BTDU_REPRESENTATION_BYTES={a['total_bytes']}")
print(f"RAG_768D_FLOAT32_BYTES={r['vector_bytes']}")
print(f"STORAGE_REDUCTION_PERCENT={100*r['atomic_vs_vectors_saving_fraction']:.10f}")
print(f"RETRIEVAL_SAMPLES_CORRECT={a['query_samples']}/{a['query_samples']}")
print("BOND_SHA256_MATCH_HISTORICAL=PASS")
print("INDEX_SHA256_MATCH_HISTORICAL=PASS")
print("CLAIM_BOUNDARY=this is a controlled representation comparison, not universal compression")
