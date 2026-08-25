#!/bin/bash
# 第二幕的可重跑版:餵一份散文規格,拿回一份結構化 spec。
#
#   ./run_act2.sh <散文規格.md> <工作目錄> [model]
#
# ⚠️ **底下那段 heredoc prompt 是受測品。** 改了它,後續的跑就不能跟先前比 ——
#    跟 interview-prompt.md / act1/ 三份是同一種性質,先前這裡沒有警語(已知缺口)。
#    每次改都要在 run 目錄留下 prompt.txt,寫報告前 diff 上一跑那份。
#    ⚠️ 靠自律記不住(shop 那跑與 timesheet 那跑的 prompt 差 43 行,沒有任何機械記錄
#    講得出這件事),所以每跑另外落一份 run-meta.json,把 prompt.txt 與其他受測輸入的
#    git blob 雜湊寫進去 —— **兩跑的報告對得起來,以 run-meta.json 的 blob 為準。**
#
# ⚠️ **交得出來 ≠ 生得出來**(2026-08-19,票 16 加第四份 architecture.yaml 時記下):
#    gen_archunit 只吃三種 kind,散文裡形狀不在那三種裡的架構規則,正確的落檔結果
#    就是 enforcement=none + ladder_note。**落檔後有數條 none 是對的,不是漏交。**
#    逐條的預測寫在 .scratch/ddd-harness/16-PREDICTION.md(那裡才可以寫具體規則,
#    這支檔案的 heredoc 是要複製給受測 agent 讀的,寫進去就是洩題)。
#
# 隔離同前:bare dir,只有散文規格 + schema + import 工具。
# **不放生成器、不放驗收 harness、不放任何既有的 acceptance.yaml** ——
# 那些是答案卷,agent 讀得到就白測了。
set -u
SPEC="$1"; WORK="$2"; MODEL="${3:-opus}"
HARNESS="$(cd "$(dirname "$0")" && pwd)"
[ -f "$SPEC" ] || { echo "找不到散文規格:$SPEC" >&2; exit 66; }

# ---- 閘門(票 21):幕一的檢查證據 -----------------------------------------
# 帳本住在幕一的 run 目錄(check.py 寫的 check-ledger.jsonl);散文規格在那個目錄裡,
# 或在它的 interviewer/ 子目錄 —— 所以往上找兩層。要求 landing_check 有一筆 exit 0。
# ⚠️ 離開碼 3(不適用)不算通過。閘門在 rm -rf "$WORK" **之前**:拒絕的話什麼都不動。
# 逃生口 ACT_GATE_SKIP=1 要附 ACT_GATE_SKIP_REASON,沒理由不准跳;跳了寫進 run-meta.json。
SPEC_DIR="$(cd "$(dirname "$SPEC")" && pwd)"
if [ "${ACT_GATE_SKIP:-0}" = "1" ]; then
  [ -n "${ACT_GATE_SKIP_REASON:-}" ] || {
    echo "ACT_GATE_SKIP=1 需要 ACT_GATE_SKIP_REASON(沒理由不准跳)" >&2; exit 2; }
  echo "⚠️ 閘門跳過(ACT_GATE_SKIP=1):$ACT_GATE_SKIP_REASON"
  GATE_SKIPPED=true
else
  python3 "$HARNESS/check.py" --gate act2 "$SPEC_DIR" "$(dirname "$SPEC_DIR")" || exit $?
  GATE_SKIPPED=false
fi
GATE_REASON_JSON="$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1], ensure_ascii=False))' \
  "${ACT_GATE_SKIP_REASON:-}")"

# ---- 儀表(票 26):上 N 跑 landing_check 不適用幾次,只印一行,不擋 --------------
# 讀 examples/**/runs/*/check-ledger.jsonl 跨跑統計(NA_RATIO_ROOT 可換掃描根,測試用)。
# 它是儀表不是閘門:沒帳本(3)、python 炸了,都不得讓 runner 失敗 —— 所以 || true。
python3 "$HARNESS/na_ratio.py" --brief --checker landing_check \
  "${NA_RATIO_ROOT:-$HARNESS/../runs}" || true

rm -rf "$WORK"; mkdir -p "$WORK/spec" "$WORK/tools/harness"
cp "$SPEC" "$WORK/spec/SPEC.md"
cp "$HARNESS/schema.sql" "$HARNESS/spec_store.py" "$WORK/tools/harness/"

cat > "$WORK/prompt.txt" <<'EOF'
你在做第二幕:落檔。把一份散文規格裡的驗收情境,轉成結構化的 spec 資料。

讀這兩個檔:
  spec/SPEC.md              —— 散文規格(來源)
  tools/harness/schema.sql  —— 結構化資料的 schema(合約)

產出四個檔案:
  acceptance.yaml   —— 頂層兩個 key:`wire_contract` 與 `acceptance_scenarios`
  glossary.yaml     —— 頂層兩個 key:`glossary_terms` 與 `banned_synonyms`
  contracts.yaml    —— 頂層一個 key:`domain_contracts`
  architecture.yaml —— 頂層兩個 key:`authorized_templates` 與 `architecture_rules`

散文裡沒有那一節的話,對應的檔就不要產 —— **不要為了交差生一份空的或湊出來的**。

**一、`wire_contract`** —— 這份規格對外的 JSON 長什麼樣。**規格擁有它,實作照做。**
散文若把 HTTP 形式標成「本案自決」,那就由你逐欄決定並寫在這裡;不要留空。
必填:name / req_customer_field / req_items_field / req_product_field /
req_quantity_field / req_price_field / req_currency_field / res_order_id_field /
list_fields(列表一列有哪些欄位)。
選填:req_total_field(請求可以夾帶總金額時才有)。
**條件式必填**(不是選填,用得到就一定要有,否則對應的檢查會靜靜地不適用):
  - `res_total_field`(列表的總金額欄)—— **只要有任何一條 list_field_equals_number
    斷言就必須給**。「總額 = Σ(數量 × 單價)」那條不變式靠它認人,沒給就永遠不檢查。
  - `res_customer_id_field`(列表的客人編號欄)—— **只要有任何一條預期被拒的情境
    就必須給**,因為每個被拒的請求都要有 list_no_row_for_customer,而它比對這一欄。
    列表若真的不揭露客人編號,那這份規格就斷言不了「沒有殘骸」,要在散文裡講明。

**二、`acceptance_scenarios`** —— 每個情境:
  - id / given_when / then_expect / provenance / provenance_ref
  - **預期成功的情境**:steps + assertions
    - steps 每個有 alias / customer_id / items(list),
      可選 claimed_total_cents(請求夾帶、系統該忽略的總金額)
    - items 每個有 product_id / quantity / unit_price_cents / currency
    - assertions 每個有 kind / target(指向某個 alias)與該 kind 的參數
      (field / expected_text / expected_number);field 必須出現在 list_fields
  - **預期被拒的情境**:`expects_rejection: true` + rejected_requests +
    rejected_assertions(**不要用 steps / assertions**)
    - rejected_requests 每個有 alias / customer_id / items,可選 claimed_total_cents。
      **這裡的值可以是不合法的** —— 數量 0 或負數、items 空的、customer_id 是空字串,
      那正是負面情境要送出去的東西,不要替它修正。
    - rejected_assertions 的 kind 只有兩個:status_is(帶 expected_number)與
      list_no_row_for_customer(無參數)。**兩個都要有** ——
      只斷言狀態碼的話,「回了 400 但還是寫了一筆」會通過。
    - 拒絕情境用的 customer_id **不得**出現在任何預期成功的情境。

情境的 fixture 若不包含 given_when 描述的那個動作(例如 schema 沒有「調整商品單價」
這個動作,你改用別的東西近似它),必須填 `proxy_for` 說明你用什麼代替了什麼。

**三、`glossary.yaml`** —— 散文的詞彙表那一節。

`glossary_terms` 每個:term / definition / ddd_type / representation / wire_field /
provenance / provenance_ref。
  - `ddd_type` 是**自由文字**,照散文寫的搬,不要硬塞進一套別的分類。
  - `wire_field` 要是**一個真的欄位名**(識別字)。散文那一格若寫的是註記或說明,
    就**留空**。⚠️ **留空 = 這個詞不上線(界外概念、或本案的 API 不揭露它),
    不是漏填** —— 不要為了填滿而猜一個欄位名。

`banned_synonyms` 每個:banned / use_instead / no_replacement_note / note。
  - `use_instead` 必須是 `glossary_terms` 裡**真的存在**的一個 term。
  - 某個講法在本案**沒有**替代詞(它指的東西這裡不存在),就留空 `use_instead`、
    改寫 `no_replacement_note` 說明為什麼。**不要硬指一個最接近的詞。**

**四、`contracts.yaml`** —— 散文的領域契約(前置條件 / 後置條件 / 不變式)那一節。

`domain_contracts` 每個:id / kind / statement / provenance / provenance_ref /
guarded_in / crosses_aggregate / disposition / enforcement / ladder_note /
named_tests / no_named_test_reason。
  - `kind` 只有 precondition / postcondition / invariant 三個。散文在型態後面加的
    括號註記是 statement 的一部分,不要拿來擴充這三個值。
  - `guarded_in` = **守在哪個物件內**。不一定是聚合根 —— 有的契約守的是某個
    Value Object 自身。
  - 判定這條需要看那個物件**以外**的資料時,`crosses_aggregate: 1`,
    而且 `disposition` 必填。⚠️ **處置要寫本文**(打算怎麼處理、殘留什麼風險),
    **不要寫「見某某節」** —— 指標下游沒有人會去讀。
  - `enforcement` 目前只能是 `none`(還沒有任何生成器讀這張表),
    而 none 時 `ladder_note` 必填:為什麼還沒有機械檢查、搬得上去的話搬去哪。
  - `named_tests` 是散文指名的驗收情境編號,必須指得到 `acceptance_scenarios` 裡
    真的存在的 id。指不出來(散文沒指名、或指的不是情境)就留空,
    改寫 `no_named_test_reason` 說明是哪一種。
    ⚠️ **兩種零很不一樣**:「散文根本沒指名」與「指名了但那個情境本檔沒有」,
    要在理由裡分清楚,不要都寫成「沒有」。

**五、`architecture.yaml`** —— 散文的架構那一節(分層、依賴方向、什麼不得存在)。

`authorized_templates` —— 被授權為「架構模板」的**文件名**白名單。
  ⚠️ **散文沒有指名任何被授權為架構模板的文件時,這裡必為空(`[]`)。**
  它不是可有可無的欄位,而是一份白名單:`provenance: 模板既定` 只能指向這份白名單
  裡的文件,**白名單是空的時候,`模板既定` 這個值物理上寫不進去** —— schema 的
  trigger 會 ABORT,整份 import 一條都不會進。⚠️ **這份白名單管住的是上面每一節** ——
  架構規則、驗收情境、領域契約、詞彙表,凡是帶 provenance 的都吃它,不只架構這一節。
  所以這個案子自己決定的架構,出處一律寫 `本案自決`,並在 provenance_ref 寫依據。
  **不要把自決包裝成既定** —— 那不是措辭問題,是把「這件事是誰決定的」記錯,
  而下游會拿它當「已經有人審過」看待。

`architecture_rules` 每個:id / rule / provenance / provenance_ref /
enforcement / ladder_note,再加上該 kind 的參數。
  - `id` 決定生成順序(排序穩定 → 生成物可 diff),用穩定可排序的編號。
  - `rule` 是**一句話、可判定**的敘述。
  - `provenance` 同前五個值之一;`provenance_ref` 空的寫不進去。
  - `enforced_by`(由誰強制)**不准自己填** —— 那一欄由生成器回填,import 會拒收。
    ⚠️ 散文的「由誰強制」欄裡若寫了測試名,**那是散文作者取的名字,不是 enforcement
    的值**;有幾條指名了測試,不代表落檔後就有幾條有機械檢查。
  - `enforcement` 的值域**只有四個**(⚠️ 跟上一節的領域契約不同,那邊目前只能 `none`):
      `archunit_forbidden_dependency`  —— 某個 package 底下不得依賴另外幾個 package
      `archunit_forbidden_annotation`  —— 某個 package 底下的類別與其欄位、方法、
                                          建構子,不得掛來自另外幾個 package 的 annotation
      `archunit_forbidden_return_type` —— 某個 package 底下、類名以某個字尾結束的類別,
                                          其 public 方法不得回傳另外幾個 package 的型別
      `none`                           —— 目前沒有機械檢查
  - **選了前三種之一,就必須帶、而且只准帶那一種的參數區塊**:
      forbidden_dependencies:  { from: <pkg>.., to: [<pkg>.., …] }
      forbidden_annotations:   { from: <pkg>.., annotations: [<pkg>.., …] }
      forbidden_return_types:  { from: <pkg>.., class_name_suffix: <類名字尾>,
                                 return_packages: [<pkg>.., …] }
    ⚠️ 每個 package pattern **一律以 `..` 結尾**(ArchUnit 的寫法),漏了寫不進去。
  - **`enforcement: none` 時不准帶任何參數區塊,而 `ladder_note` 必填**:
    為什麼還沒有機械檢查、搬得上去的話缺的是哪一種 kind。

⚠️ **交得出來 ≠ 生得出來。** 生成器只吃上面那三種形狀。散文裡形狀不在那三種裡的規則
(「必須存在什麼」、「某種東西不得存在」、「某條路徑只讀不寫」這類),
**老實標 `enforcement: none`、把理由寫進 ladder_note**。硬掰成三種之一,只會生出
一條檢查不到那件事的測試 —— 那比沒有更糟,因為它會綠。
**落檔後有數條 `none` 是正常的,不要為了好看去湊。**

驗證你的產出:

    python3 tools/harness/spec_store.py import acceptance.yaml glossary.yaml contracts.yaml architecture.yaml /tmp/spec.db

(只產得出其中幾份的話,就只列你真的產出的那幾份。)

它會印出逐條錯誤。**改到它印 ok 為止**,那是完成的定義。

規則:
- provenance 只能是 schema 允許的五個值之一;provenance_ref 要指得出 SPEC.md 的行號。
- 「模板既定」只有在 `authorized_templates` 指得出授權文件時才用得上,見第五節。
- 只做 SPEC.md 裡實際寫出來的情境,不要自己加。
- 除了上面兩個檔和你自己產出的那幾份 yaml,不要讀這個目錄的其他檔案。

輸出繁體中文的註解即可,欄位名用 schema 的英文名。
EOF

# ---- 這一跑吃了什麼:run-meta.json ----------------------------------------
# 形狀照第一幕的 orchestrate.py(input_blobs / 跑之前就寫),不另立一套。
# **時機是重點**:prompt.txt 是上面那段 heredoc 剛寫出來的,SPEC.md / schema.sql /
# spec_store.py 是開頭那幾行 cp 進去的 —— 四份都就位了才算得準,而且必須算在
# 呼叫 claude **之前**:agent 在 $WORK 底下是 bypassPermissions,事後再算,算到的
# 可能是它動過的版本,那就不是「受測輸入」了。
blob() {
  # 認不出來就寫 unknown —— 不要猜(同 orchestrate.py 的 input_blobs)。
  # git hash-object 對 repo 外的任意檔案也算得出來,所以 $WORK 放哪都行。
  git hash-object "$1" 2>/dev/null || echo unknown
}
SPEC_ABS="$(cd "$(dirname "$SPEC")" && pwd)/$(basename "$SPEC")"
# 註:路徑或 model 名含 `"` 或 `\` 會拼出壞 JSON。本 repo 的路徑不長那樣。
# 跳閘門的理由是人打的自由文字,那格用 python3 的 json.dumps 逃脫(閘門本來就要 python3)。
cat > "$WORK/run-meta.json" <<META
{
  "model": "$MODEL",
  "spec": "$SPEC_ABS",
  "gate_skipped": $GATE_SKIPPED,
  "gate_skip_reason": $GATE_REASON_JSON,
  "input_blobs": {
    "prompt.txt": "$(blob "$WORK/prompt.txt")",
    "tools/harness/schema.sql": "$(blob "$WORK/tools/harness/schema.sql")",
    "tools/harness/spec_store.py": "$(blob "$WORK/tools/harness/spec_store.py")",
    "spec/SPEC.md": "$(blob "$WORK/spec/SPEC.md")"
  }
}
META

# 只組工作目錄、不呼叫 claude(不花錢)—— 閘門與 run-meta.json 的測試靠這條路。
if [ "${ACT2_DRY_RUN:-0}" = "1" ]; then
  echo "dry-run:工作目錄組好了,沒有呼叫 claude"
  echo "  spec     : $WORK/spec/SPEC.md"
  echo "  prompt   : $WORK/prompt.txt"
  echo "  run-meta : $WORK/run-meta.json"
  echo "  model    : $MODEL(未使用)"
  exit 0
fi

cd "$WORK" || exit 90
env -i HOME="$HOME" PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/bin:/bin" \
    USER="$USER" SHELL=/bin/bash TERM=dumb LANG=en_US.UTF-8 WORK="$WORK" MODEL="$MODEL" \
  bash -c '
    cd "$WORK"
    claude -p "$(cat prompt.txt)" --model "$MODEL" --safe-mode \
      --permission-mode bypassPermissions --output-format json
  ' > "$WORK/result.json" 2> "$WORK/stderr.log"
rc=$?
[ -f "$WORK/acceptance.yaml" ] && echo "ok: $WORK/acceptance.yaml" || echo "rc=$rc:沒有產出 acceptance.yaml"
