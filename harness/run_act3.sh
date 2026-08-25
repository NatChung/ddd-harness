#!/bin/bash
# 第三幕的 runner:生成之前先查幕二的檢查證據(票 21)。
#
#   ./run_act3.sh <spec.db> <輸出目錄>
#
# 閘門讀 <spec.db> 所在目錄的 check-ledger.jsonl(幕二的 run 目錄),要求:
#   spec_store import 有一筆 exit 0;provenance_check / contract_triage / glossary_check
#   各至少跑過一筆(那三支交的是分診佇列,離開碼不拘,只要求跑過)。
# ⚠️ 離開碼 3(不適用)不算通過 —— 閘門判準是 exit == 0。
#
# 閘門為什麼在這裡、不在 gen_*.py 的 main() 裡:test_harness.py 直接呼叫兩支生成器的
# main() 釘離開碼,生成器本體不動。**所以直接跑 gen_*.py 是繞得過閘門的** —— 這條
# runner 才是幕三該用的入口,PIPELINE.md 的指令段只寫它。
#
# 兩支生成器的離開碼各自傳出來:任一 1 / 2 → 那個碼;任一 3(不適用)→ 3;都 0 → 0。
# 逃生口同 run_act2.sh:ACT_GATE_SKIP=1 + ACT_GATE_SKIP_REASON,留痕在 <輸出目錄>/run-meta.json。
set -u
if [ $# -ne 2 ]; then
  echo "用法:$0 <spec.db> <輸出目錄>" >&2
  exit 64
fi
DB="$1"; OUT="$2"
HARNESS="$(cd "$(dirname "$0")" && pwd)"
[ -f "$DB" ] || { echo "找不到 spec store:$DB" >&2; exit 66; }
DB_DIR="$(cd "$(dirname "$DB")" && pwd)"
DB_ABS="$DB_DIR/$(basename "$DB")"

# ---- 閘門(票 21):幕二的檢查證據 -----------------------------------------
if [ "${ACT_GATE_SKIP:-0}" = "1" ]; then
  [ -n "${ACT_GATE_SKIP_REASON:-}" ] || {
    echo "ACT_GATE_SKIP=1 需要 ACT_GATE_SKIP_REASON(沒理由不准跳)" >&2; exit 2; }
  echo "⚠️ 閘門跳過(ACT_GATE_SKIP=1):$ACT_GATE_SKIP_REASON"
  GATE_SKIPPED=true
else
  python3 "$HARNESS/check.py" --gate act3 "$DB_DIR" || exit $?
  GATE_SKIPPED=false
fi
GATE_REASON_JSON="$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1], ensure_ascii=False))' \
  "${ACT_GATE_SKIP_REASON:-}")"

mkdir -p "$OUT"
cat > "$OUT/run-meta.json" <<META
{
  "spec_db": "$DB_ABS",
  "gate_skipped": $GATE_SKIPPED,
  "gate_skip_reason": $GATE_REASON_JSON
}
META

python3 "$HARNESS/gen_archunit.py"   "$DB_ABS" "$OUT/ArchitectureTest.java";   rc_arch=$?
python3 "$HARNESS/gen_acceptance.py" "$DB_ABS" "$OUT/OrderAcceptanceTest.java"; rc_acc=$?
echo "gen_archunit exit $rc_arch / gen_acceptance exit $rc_acc"

for rc in "$rc_arch" "$rc_acc"; do
  case "$rc" in 1|2) exit "$rc" ;; esac
done
for rc in "$rc_arch" "$rc_acc"; do
  [ "$rc" = "3" ] && { echo "有生成器不適用 —— 不是通過"; exit 3; }
done
exit 0
