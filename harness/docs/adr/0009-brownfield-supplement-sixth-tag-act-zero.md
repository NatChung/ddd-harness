# ADR 0009 — Brownfield:訪談 prompt 用補充檔不分叉;來源標記加第六格;幕零從既有 code 抽候選表

## Status

**Proposed**(2026-08-25)—— 落地票等第一個 hub feature 選定再開(vpin-hub 或 kc-hub)。
與 ADR 0008 的關係:本 ADR **不動** `harness/interview-prompt.md`,所以不撞 0008 的 blocked
條件;0008 解 blocked 後,它那兩格(Aggregate 判準、BC 對外 API / 整合模式)要不要也進補充檔,另決。

## Context

這套 harness 是 greenfield 長出來的(`examples/shop`:一句需求、沒有既有系統)。它假設規格只有一個來源
——需求方的嘴。vpin-app / kc-app / kc-web 是 brownfield:**既有 code 是第二個來源**,而且常常是唯一
記得規則的地方。今天的儀器對它有四個不合:

1. `act1/interviewer/prompt.txt` 寫死「沒有既有系統、沒有架構模板」。
2. 來源標記只有五格,`interview-prompt.md` §二明文「不得自創第六格」,`schema.sql` 三處 CHECK
   (`:31` architecture_rule、`:183` acceptance_scenario、`:407` domain_contract,逐字相同)擋死。
   **從既有 code 讀出來的規則沒地方標。**
3. 訪談者不知道 code 裡已經有 `Booking` / `Checkout`,會問出第二套詞 —— 正是 Ubiquitous Language 要擋的事。
4. 兩個 greenfield 沒有的情況:**server 還沒做**(app / web 對著不存在的 API)、**UI 要人眼確認**
   (「看起來對」機器判不了)。今天的 §2 GWT 與 `wire_contract` 沒有格子放它們。

對照(驗過,`docs/research/2026-08-25-harness-survey.md`):Agentheim ADR-0061 的 `[human-eye]`
標記 —— 只有人能判的驗收條目明標、checkbox 永不由機器打勾、verifier 永不代理;
mattpocock `/domain-modeling` 的「使用者說 X 怎麼運作,查 code 同不同意,不同就攤出來」那條規則。

## Decision

### 1. 補充檔,不分叉、不改正本

`interview-prompt.md` 一字不動。新增 **`harness/interview-brownfield.md`**,只載**差量**:第六格、
候選表怎麼讀、對 code 查證那條規則、`[human-eye]`、提供方狀態。Brownfield 的 template_dir 多放這一份,
`orchestrate.stage_inputs()` 整包複製會自動帶上(它的 docstring 就是為這種情況寫的);訪談者的開場
prompt 多一句「先讀 `interview-brownfield.md`,它補充而不取代工作指示」。

為什麼不分叉(像 `examples/returns/` 那樣整份複製):兩份散文講同一條規則會漂(`CLAUDE.md` 硬規則、
2026-08-25 刪 spec-authoring skill 的理由)。補充檔只有差量,正本改了它不用跟。
為什麼不直接改正本:`PIPELINE.md`〈現在缺的〉第 1 項 opus 那跑量的是現在這份,改了就量另一支儀器
(ADR 0008 同一個理由)。

### 2. 第六格:`既有程式碼 <file:line>`,而且確認後**不洗白**

- 標記:`既有程式碼 <repo>/<path>:<line>`。指的是**規則被讀出來的那行**,不是相關的檔。
- **不洗白規則**:幕零抽出來的值,經需求方確認後**仍標第六格**,確認記在旁邊 ——
  `既有程式碼 app/lib/order.dart:41,經 [Q3] 確認`。**不得**改成單純 `[Q3]`。
  理由:`provenance_check` 抓到過「訪談者餵值再標成親口確認」(opus 那場 100/120);幕零是同一個
  失效的新變體 —— 訪談者把 code 的值念給需求方聽,他說「對」,來源就變成 `[Qn]`,code 的出處消失。
  沒有這條,第六格是裝飾。**這是落地票 PREDICTION 的第一條:訪談者會不會把 code 值洗成 `[Qn]`。**
- 需求方**不認** code 裡的規則:標 `既有程式碼 X:12,需求方未確認`,進 §7 矛盾或 §5 規格沉默,
  **不調和**。這一格是 brownfield 最值錢的產出:code 裡沒人記得為什麼的規則清單。

### 3. Schema:三處 CHECK 擴成六格;`wire_contract` 加提供方狀態;情境加 `human_eye`

- `schema.sql:31 / :183 / :407` 的 `provenance CHECK IN (...)` 加 `'既有程式碼'`;三處**逐字相同**的約定
  照舊(ADR 0005 共同形狀)。Greenfield 的 spec 就是不用第六格,不需要分 schema。
- 新 trigger `code_provenance_ref_shape`:`既有程式碼` 的 `provenance_ref` 必須符合 `<path>:<digits>`
  (形狀查得到;檔存不存在、行號在不在範圍,是第 2 階報告 —— 與 `referenced-run-exists` 同形,先延後)。
- `wire_contract` 加 `provider_status TEXT NOT NULL CHECK (provider_status IN ('已實作','替身','形狀未定'))`。
  `形狀未定` = 阻斷級:對應的情境與契約進 §10「不得開工的部分」;`gen_acceptance` 對它**不生成、印不適用**。
  `替身` = 形狀定了、server 沒寫:app / web 對 HTTP 假服務(ADR 0006 §2)做到全綠;server 做好後
  同一份 `wire_contract` 生它那邊的驗收。**「server 沒寫」不擋,「形狀沒定」才擋。**
- `acceptance_scenario` 加 `human_eye INTEGER NOT NULL DEFAULT 0 CHECK (human_eye IN (0,1))`。
  `human_eye = 1` 的情境:`gen_acceptance` **不生測試**、`acceptance_gwt` 報表自成一類「待人眼確認 N 條」,
  **永不折進通過**;規格裡要寫**誰**確認、確認**什麼**。禁止用機器指標代理(截圖相似度不是「看起來對」)
  —— `CONTEXT.md`「代理編碼↔假驗收」在 UI 上的樣子。
- 幕二受測輸入變了:`PIPELINE.md` 幕二「2026-08-25 起不得與之前比基線」那句已涵蓋。

### 4. 幕零:從既有 code 抽候選表,只切一片

新腳本 `harness/act0_extract.py <repo> <slice>`,用 codegraph 抽**一個 Bounded Context 那一片**
(不對整個 app 建表;片外的 code 當外部系統):

| 抽什麼 | 從哪 | 進哪 | 標記 |
|---|---|---|---|
| class / enum / 欄位名;同時存在的近義名 | 型別定義 | `glossary_term` 候選 + 禁用同義詞題 | 第六格 |
| package / import 方向 | 相依圖 | `architecture_rule` **現況**(不是理想) | 第六格 |
| request / response 形狀 | route / DTO | `wire_contract` 現況,`provider_status = 已實作` | 第六格 |
| `throw` / guard / early return | 守衛 | `domain_contract` 候選,型態待訪談判 | 第六格 |
| 既有測試 | test 檔 | `acceptance_scenario` 候選 | 第六格 |

產出 `act0-candidates.yaml`,是**幕一的輸入**,不直接進 store(進 store 的是訪談確認過的)。
架構檢查對既有 code 一定紅一片,所以 brownfield 的架構規則要**「不變差」而非「全綠」**——
survey §5 (c) sentrux 那招在這裡對了(greenfield 判不抄,是因為沒東西比)。

三個 mattpocock skill 的位置:`/improve-codebase-architecture` 可選、用來**挑切哪一片**(又熱又亂);
`/domain-modeling` 的「對 code 查」規則抄進補充檔,它的 `CONTEXT.md` 格式**不採用**(少型態、單位、來源四欄);
`/codebase-design` 幕四才用(替身 server 的 adapter 放哪)。三個都不做抽取,抽取要自己寫。

### 5. Hub 開工 prompt 只有一份正本

`harness/hub-bootstrap.md` 住 ddd-harness;vpin-hub / kc-hub 以 submodule 引用 ddd-harness,
**不複製**進 hub。Hub 自己的 `AGENTS.md` 只寫一句指過來。理由同 §1。

## 由誰強制(ADR 0007)

| 項 | 守法 |
|---|---|
| 第六格寫得進 store | schema CHECK(第 1 階) |
| 第六格 `provenance_ref` 形狀 | trigger(第 1 階);檔與行號存在 → 第 2 階報告,**延後,prose-only** |
| 確認後不洗白 | `provenance_check` 新段:候選表裡的值在 spec 裡標成純 `[Qn]` → 佇列(不是判決) |
| `形狀未定` 不生成、不實作 | `gen_acceptance` 印不適用;§10 不得開工清單 —— 後者 prose-only |
| `human_eye` 不折進通過 | `acceptance_gwt` 報表自成一類;`gen_acceptance` 不生 |
| 幕零抽取規則 | **prose-only, unenforced**(抽漏了只能靠訪談補) |
| 補充檔與正本不重複 | prose-only;若日後漂,回頭做 `harness_lint` 規則「補充檔不得含正本已有的段落標題」 |

## Consequences

- 動的是受測品(schema、補充檔、生成器、兩支檢查器)。落地票要先寫 PREDICTION,第一條釘洗白。
- 第一個 brownfield run 的 `run-meta.json` 要記 `interview-brownfield.md` 的 blob,與 `interview-prompt.md` 分開記。
- vpin / kc 的線不與 `examples/shop` 比基線 —— 儀器不同(多一份輸入)。
- **沒驗過的**:候選表會不會太大讓訪談者照抄;`[human-eye]` 會不會被拿來逃避寫可測的 GWT
  (Agentheim 對此的答法是「先試著磨成可測的,`[human-eye]` 是最後手段」—— 抄進補充檔)。
