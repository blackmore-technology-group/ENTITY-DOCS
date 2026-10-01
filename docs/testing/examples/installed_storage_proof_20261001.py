from pathlib import Path
import shutil, sys, json
INSTALLED=Path(r'E:\ENTITY_ACTIVE\BTG_BUILT_LOCALAPPDATA\BTG\ADAM_RC2\ADAM_v1_0_COMPLETE_SOFTWARE_REFERENCE_RC2')
OUTPUT=Path(r'E:\ENTITY_ACTIVE\ENTITY_STORAGE_PROOF_20261001\installed')
sys.path.insert(0,str(INSTALLED))
from adam_v41.audit import run_audit
if OUTPUT.exists(): shutil.rmtree(OUTPUT)
OUTPUT.mkdir(parents=True,exist_ok=True)
print(f'INSTALLED_STORAGE_PROOF_START root={INSTALLED}',flush=True)
result=run_audit(OUTPUT,records=1500,seed=20260804)
(OUTPUT/'INSTALLED_STORAGE_PROOF_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
print('ENTITY_STORAGE_TEST=PASS' if result['overall_pass'] else 'ENTITY_STORAGE_TEST=FAIL',flush=True)
print(f"CHECKS={result['checks_passed']}/{result['checks_total']}",flush=True)
for row in result['workloads']:
 print(f"WORKLOAD={row['mode']}",flush=True)
 print(f"SQLITE_BYTES={row['sqlite_current_bytes']}",flush=True)
 print(f"FACTORED_BYTES={row['adam_native_factored_state_bytes']}",flush=True)
 print(f"FACTORED_REDUCTION_PERCENT={row['native_factored_vs_sqlite_reduction_percent']:.6f}",flush=True)
 print(f"EXACT_VIEW={'PASS' if row['views_equal'] else 'FAIL'}",flush=True)
 print(f"RESTART_RECOVERY={'PASS' if row['checkpoint_restart_pass'] else 'FAIL'}",flush=True)
print(f"HIGH_ENTROPY_EXPANSION_PERCENT={result['high_entropy']['expansion_percent']:.6f}",flush=True)
