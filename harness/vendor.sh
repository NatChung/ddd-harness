#!/bin/bash
# 把 harness/ 搬進一個 hub —— 用 copy,不用 submodule / sparse-checkout(票 32、ADR 0010)。
#
#   ./vendor.sh <hub-dir>
#
# 為什麼是 copy:hub(kc-hub、vpin-hub …)拿走 harness 之後各自發展,**不回流上游**,
# 兩個 hub 也不該互相污染。submodule 讓 hub 改一行就得回上游 commit;手工挑檔搬
# (2026-08-26 kc-hub 那次)每個 hub 搬出來都不一樣。這支把「搬」變成一個機械步驟:
#
#   1. copy `harness/` → `<hub-dir>/harness/`(排除 __pycache__ / .pytest_cache / ORIGIN.md)
#   2. 寫 `<hub-dir>/harness/ORIGIN.md`:來源 repo、commit、日期、搬的方式
#   3. 在副本裡跑 pytest,把結果那行印出來並追加進 ORIGIN.md —— 副本沒驗過不算搬完
#
# 離開碼:
#   0  搬完,副本 pytest 綠
#   1  拒絕或未驗證:<hub>/harness 已存在(不覆蓋)、上游 harness/ working tree 髒、
#      不是 git repo / 沒有 git、pytest 不在、副本 pytest 紅(副本**留著**,方便看)
#   2  用法錯誤:沒給 <hub-dir>,或它不是既有目錄
#
# 為什麼髒的 working tree 要拒絕:ORIGIN.md 記的是 HEAD 的 commit hash,但 copy 的是
# working tree —— 樹髒了那個 hash 就是謊話,之後 hub 要 diff 上游會對不到。
# 逃生口 VENDOR_ALLOW_DIRTY=1(開發 harness 本身、還沒 commit 就想試搬的時候用)。
#
# 遞迴防線:副本裡也有 test_vendor.py(hub 可能再往下搬),它會再跑一次 vendor.sh、
# 再在副本裡跑 pytest……無限下去。所以這裡跑副本 pytest 時帶 VENDOR_INNER=1,
# test_vendor.py 看到這個環境變數就整個模組 skip。
set -euo pipefail

HARNESS="$(cd "$(dirname "$0")" && pwd)"
UPSTREAM="$(cd "$HARNESS/.." && pwd)"

# ---- 用法 ------------------------------------------------------------------
if [ $# -ne 1 ]; then
  echo "用法:$0 <hub-dir>" >&2
  exit 2
fi
if [ ! -d "$1" ]; then
  echo "用法:$0 <hub-dir> —— <hub-dir> 要是既有目錄,拿到的是:$1" >&2
  exit 2
fi
HUB="$(cd "$1" && pwd)"
DST="$HUB/harness"

# ---- 拒絕:已存在 -------------------------------------------------------------
if [ -e "$DST" ]; then
  echo "$DST 已存在,不覆蓋 —— 要更新請手動 diff,見 ORIGIN.md" >&2
  exit 1
fi

# ---- 拒絕:沒 git / 不是 repo / 樹髒 ----------------------------------------
if ! command -v git >/dev/null 2>&1; then
  echo "找不到 git —— ORIGIN.md 要記來源 commit,沒 git 記不了" >&2
  exit 1
fi
if ! git -C "$UPSTREAM" rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "$UPSTREAM 不是 git repo(或還沒有任何 commit)—— ORIGIN.md 要記來源 commit" >&2
  exit 1
fi
DIRTY="$(git -C "$UPSTREAM" status --porcelain -- harness)"
if [ -n "$DIRTY" ]; then
  if [ "${VENDOR_ALLOW_DIRTY:-0}" = "1" ]; then
    echo "⚠️ 上游 harness/ working tree 髒,VENDOR_ALLOW_DIRTY=1 照搬 —— ORIGIN.md 的 commit 跟副本內容可能對不上"
  else
    echo "上游 harness/ working tree 髒,拒絕搬:ORIGIN.md 記的 commit 會跟副本內容對不上。" >&2
    echo "先 commit,或 VENDOR_ALLOW_DIRTY=1 強搬(自己負責)。髒的:" >&2
    printf '%s\n' "$DIRTY" >&2
    exit 1
  fi
fi

SHA="$(git -C "$UPSTREAM" rev-parse HEAD)"
SHORT="$(git -C "$UPSTREAM" rev-parse --short HEAD)"
REMOTE="$(git -C "$UPSTREAM" remote get-url origin 2>/dev/null)" || REMOTE="(沒有 origin remote)"
TODAY="$(date +%F)"

# ---- copy ----------------------------------------------------------------------
if command -v rsync >/dev/null 2>&1; then
  rsync -a --exclude __pycache__ --exclude .pytest_cache --exclude ORIGIN.md "$HARNESS/" "$DST/"
else
  cp -R "$HARNESS" "$DST"
  find "$DST" -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
  rm -f "$DST/ORIGIN.md"
fi

# ---- ORIGIN.md(先寫 metadata;pytest 那行最後追加,紅了也留得下紀錄)-------------
ORIGIN="$DST/ORIGIN.md"
cat > "$ORIGIN" <<EOF
# ORIGIN —— 這份 harness 從哪來

- 來源 repo:$REMOTE
- 來源 commit:$SHA($SHORT)
- 日期:$TODAY
- 搬的方式:\`harness/vendor.sh\`(copy,不是 submodule)

之後在 hub 裡各自發展,不跟上游同步;要撿上游改動就手動 diff:

    diff -r --exclude=__pycache__ --exclude=ORIGIN.md <上游>/harness harness

EOF

# ---- 副本 pytest --------------------------------------------------------------
if ! python3 -c 'import pytest' >/dev/null 2>&1; then
  echo "- vendor 當下 pytest:pytest 不在,沒跑" >> "$ORIGIN"
  echo "pytest 不在,副本沒驗過 —— 副本留在 $DST,裝好 pytest 自己跑一次" >&2
  exit 1
fi
OUT="$(cd "$DST" && VENDOR_INNER=1 python3 -m pytest -q -p no:cacheprovider 2>&1)" && RC=0 || RC=$?
LINE="$(printf '%s\n' "$OUT" | tail -n 1)"
find "$DST" -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
echo "- vendor 當下 pytest:$LINE" >> "$ORIGIN"

if [ "$RC" -ne 0 ]; then
  printf '%s\n' "$OUT" >&2
  echo "副本 pytest 紅(exit $RC)—— 副本留在 $DST 方便看,但這不算搬完" >&2
  exit 1
fi

# ---- 結果 ------------------------------------------------------------------------
echo "搬到:$DST"
echo "來源 commit:$SHA($SHORT)"
echo "副本 pytest:$LINE"
exit 0
