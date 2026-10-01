from pathlib import Path
import shutil, sys

INSTALLED = Path(r"E:\ENTITY_ACTIVE\BTG_BUILT_LOCALAPPDATA\BTG\ADAM_RC2\ADAM_v1_0_COMPLETE_SOFTWARE_REFERENCE_RC2")
OUTPUT = Path(r"E:\ENTITY_ACTIVE\ENTITY_TESTING_20261001\runs\storage-efficiency")
sys.path.insert(0, str(INSTALLED))
from adam_v41.audit import run_audit

if OUTPUT.exists():
    shutil.rmtree(OUTPUT)
result = run_audit(OUTPUT, records=1500, seed=20260804)
print("ENTITY_STORAGE_TEST=PASS" if result["overall_pass"] else "ENTITY_STORAGE_TEST=FAIL")
print(f"CHECKS={result['checks_passed']}/{result['checks_total']}")
for row in result["workloads"]:
    print(f"WORKLOAD={row['mode']}")
    print(f"SQLITE_BYTES={row['sqlite_current_bytes']}")
    print(f"FACTORED_BYTES={row['adam_native_factored_state_bytes']}")
    print(f"FACTORED_REDUCTION_PERCENT={row['native_factored_vs_sqlite_reduction_percent']:.6f}")
    print(f"EXACT_VIEW={'PASS' if row['views_equal'] else 'FAIL'}")
    print(f"RESTART_RECOVERY={'PASS' if row['checkpoint_restart_pass'] else 'FAIL'}")
