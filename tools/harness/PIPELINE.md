# 管線全圖 —— 一句需求走到驗收全綠

`README.md` 只講**第三幕的生成器**。這一份講**整條線**:每一段的輸入是哪個檔、
哪支工具、產出什麼、誰檢查、**驗過沒有**。

> **最重要的欄位是「驗過沒有」。** 這條線上反覆出現的失效是「做了 ≠ 接上了 ≠ 驗過了」
> —— 要求寫進 skill 但管線不讀、揭露寫進 store 但沒生進 Java、狀態寫進內文但摘要表是舊的。
> 所以本檔每一段都要標證據,標不出來的就寫「沒驗過」。

---

## 一張圖

```
   「我要一個系統,客人能下單,我能看到所有訂單。」
                    │
   ┌────────────────▼─────────────────────────────────────────┐
   │ 幕一 訪談        orchestrate.py                            │
   │   AI 訪談者 ⇄ 需求方,N 輪 → 散文規格(真人 / agent 兩種,見下) │
   │   檢查:relay_ledger.verify(每輪答案都轉交了嗎)            │
   │   檢查:landing_check.py(轉交完有沒有記進落點表)          │
   └────────────────┬─────────────────────────────────────────┘
                    │ SPEC-draft.md(散文)
   ┌────────────────▼─────────────────────────────────────────┐
   │ 幕二 落檔        run_act2.sh → agent → acceptance.yaml     │
   │   檢查:spec_store.py import(佔位符 + schema 擋 + 跨列不變式)│
   │   檢查:provenance_check.py(來源標記的分診佇列)            │
   └────────────────┬─────────────────────────────────────────┘
                    │ spec.db(結構化,唯一真相)
   ┌────────────────▼─────────────────────────────────────────┐
   │ 幕三 生成        gen_archunit.py / gen_acceptance.py       │
   │   → ArchitectureTest / OrderAcceptanceTest                │
   │     + OrderProxyAcceptanceTest(代理編碼,不算驗收)         │
   │   檢查:verify_generated.py(生成物有沒有被手改)            │
   └────────────────┬─────────────────────────────────────────┘
                    │ 可執行的驗收
   ┌────────────────▼─────────────────────────────────────────┐
   │ 幕四 實作        agent 照 PROMPT.md 填骨架 → 驗收全綠       │
   │   檢查:acceptance_gwt.py(空骨架全紅 / 可滿足 / 逐條可紅)  │
   │   檢查:vacuous_tests.py(假驗收分診)                      │
   │   ✅ 2026-08-19 跑過一次 9/9 全綠,但真情境只有 1 條      │
   └────────────────┬─────────────────────────────────────────┘
                    │ 洞
   ┌────────────────▼─────────────────────────────────────────┐
   │ 幕五 review      洞 → 搬階 → 改 harness → 重跑證明它掉不了  │
   │   這是唯一會複利的一幕(MISSION)                           │
   └──────────────────────────────────────────────────────────┘
```

## 幕與幕之間的閘門(票 21,2026-08-25)

上面每一段的「檢查」以前都是文字約定:可以直接 `run_act4.sh` 而空骨架從沒驗過紅。
現在**擋在 runner 本身**,不是另一支「沒人被迫用」的 pipeline script:

```bash
python3 tools/harness/check.py [--run-dir <dir>] <checker> <args…>   # 跑檢查器,把離開碼記進 <run_dir>/check-ledger.jsonl
python3 tools/harness/check.py --gate act2|act3|act4 <dir> [<dir>…]  # runner 開頭呼叫的閘門:0 過 / 1 沒過 / 3 不適用
```

| runner | 讀哪裡的帳本 | 要求 |
|---|---|---|
| `run_act2.sh` | 散文規格所在目錄,或它的上一層(`interviewer/`) | `landing_check` 有一筆 `exit == 0` |
| `run_act3.sh` | `<spec.db>` 所在目錄 | `spec_store import` 有一筆 0;`provenance_check` / `contract_triage` / `glossary_check` 各至少跑過一筆 |
| `run_act4.sh` | **骨架目錄** | `acceptance_gwt` 有一筆 `exit == 0` |

- **離開碼 3 不算通過。** 閘門判準是 `exit == 0`,不是 `exit != 1`;帳本裡那筆是 3 → 閘門回 1。
- 帳本沒有那一幕的任何紀錄 → runner 印「不適用:上一幕從沒被檢查過」、離開碼 3;
  有紀錄但沒一筆 0 → 1。**兩種都在 `rm -rf` 工作目錄之前**,拒絕的話什麼都不動。
- 逃生口:`ACT_GATE_SKIP=1` + `ACT_GATE_SKIP_REASON=…`,沒理由 → 2。跳了會寫
  `gate_skipped: true` + 理由進該跑的 `run-meta.json`(`run_act4.sh` 為此新增了 run-meta.json)。
- **誰逼你用 `check.py`**:沒有人 —— 除了下一幕的閘門,沒帳本它就拒絕。這是這條慣例的機械化。
  尾端沒人守:幕四自己的檢查(`vacuous_tests` 等)不擋任何下游,**prose-only, unenforced**。
- 帳本查的是「跑過且過了」,**不查「檢查完之後東西有沒有再動」**。
- `check-ledger.jsonl` 每行 `{"checker","argv","exit","ts","cwd"}`,append-only,跟幕一的
  `relay-ledger.jsonl` 同一種形狀。格式本身 prose-only, unenforced(票 26 會讀它,讀不動就知道)。

**驗過沒有(2026-08-25,`.scratch/ddd-harness/21-RESULT.md`,全在 scratch 複本上跑)**:
- ✅ haiku roleplay 那份 `landing_check` exit 1 → `run_act2.sh` 拒絕(1),先前的工作目錄沒被動;
  同一份沒跑過檢查 → 3;opus-rerun 那份 exit 0 → 放行
- ✅ 2026-08-19-act2 那份:import + 三支分診跑過 → `run_act3.sh` 放行、生成器自己回 3(沒交 `architecture.yaml`)
- ❌ **幕四的閘門在真實素材上目前只能靠 `ACT_GATE_SKIP` 過**:`acceptance_gwt` 第一段
  `git archive 4567d31`,而 `4567d31` 與 `layered/OL1-integration` 都留在 `kc-log`、沒跟著搬
  → 它在本 repo 一跑就炸(exit 1)。就算搬過來,綁非 `shop-frozen-v1` 合約的 spec 第 2、3 段
  不適用 → 整支回 3 → 閘門照樣拒絕。修法要動檢查器本體(讓第一段能單獨回報),不在票 21。

### 不適用比率儀表(票 26,2026-08-25)

閘門把「3 不算通過」擋住了,但連續十跑都不適用,今天還是沒人會注意 —— 「不適用」被看見的前提是
有人在看。`na_ratio.py` 讀上面那些帳本跨跑統計,**它是儀表不是閘門**:離開碼只有 0 / 2 / 3,
超過門檻印 ⚠️ 不回 1(升成閘門要另開票)。

```bash
python3 tools/harness/na_ratio.py examples                                   # 表:列 = 檢查器,欄 = 跑過 / 0 / 1 / 3 / 其他 / skip / 不適用率 / 連續不適用
python3 tools/harness/na_ratio.py --brief --checker landing_check examples   # 一行,runner 開頭用
#   --warn-threshold 0.25 --min-runs 5 預設:跑過 ≥ 5 且不適用率 > 25% 才 ⚠️(抄 Harmonist 的形狀,門檻沒量過)
```

- `run_act2.sh` / `run_act4.sh` 在閘門判定**之後**、`rm -rf` 之前各印一行
  (`上 N 跑 landing_check 不適用 M 次` / `acceptance_gwt`);`|| true`,儀表失敗不得讓 runner 失敗。
  預設掃 `examples/`,`NA_RATIO_ROOT` 可換(測試用)。**不要改掃 repo root** —— 會把
  `tools/harness/fixtures/` 的合成帳本掃進去(驗過:12 份,`landing_check` 被考卷頂成 ⚠️)。
- 沒帳本的 `runs/<name>`(票 21 之前的舊 run)只印張數,**不進分母**;讀不動的行跳過並計數印出,
  不 crash;**一份帳本都沒有 → 3,不是 0**(帳本在但一筆都讀不動也是 3)。
- `skip` 欄是**推斷**:`run-meta.json` 有 `gate_skipped: true` 的跑,幕別從欄位形狀猜
  (`skeleton` → act4、`spec_db` → act3、`spec` → act2),對到 `check.GATES` 那幕要求的檢查器。
- 帳本格式仍歸票 21,這支只讀。`run_act3.sh` 沒有那一行(票只點名 act2 / act4)。

**驗過沒有(2026-08-25,`.scratch/ddd-harness/26-RESULT.md`,預測 7 條命中 7)**:
- ✅ 對現有 18 張 run:一份帳本都沒有 → exit 3、印「舊 run 18 張」;runner 那行在「上一幕的檢查證據齊了」之後印出同一句(opus-rerun 的 scratchpad 複本,dry-run)
- ✅ 儀器行為靠合成帳本釘:`fixtures/exams/na_ratio/` 6 case(正常 / 超門檻仍 exit 0 / 零帳本 3 / 讀不動的行 / 全讀不動 3 / 用法錯誤)+ `test_na_ratio.py`
- ❌ **趨勢本身在真實素材上量不到** —— 帳本要等票 21 之後的跑累積;門檻 0.25 / 5 對本 repo 合不合適沒量過

---

## 幕一:訪談

需求方有兩種,不要混:**正式那跑(2026-08-19)需求方是真人**,訪談者是 bare dir 裡的
subagent,轉述者手動轉交、帳本手建——**沒走 `orchestrate.py`**。下面這支是
**agent 扮需求方**的儀器測試模式(它會現編細節,票 04;證據見本節末的「驗過沒有」)。

```bash
python3 tools/harness/orchestrate.py <run_dir> examples/shop/harness/act1 [rounds]
# model 預設 opus(訪談者)/ sonnet(需求方);用環境變數換:
# INTERVIEWER_MODEL=haiku STAKEHOLDER_MODEL=haiku …
```

```bash
python3 tools/harness/check.py landing_check <run_dir> [<run_dir>/SPEC-draft.md]   # 記進 <run_dir>/check-ledger.jsonl,run_act2.sh 的閘門讀它
```

**受測輸入 4 份,全部由 `stage_inputs()` 機械複製**(手動放檔案就是接錯的原因):

| 檔 | 正本位置 | 是什麼 |
|---|---|---|
| 訪談者的工作指示 | `tools/harness/interview-prompt.md` | 12.6K,四條鐵律 + 追問表 + 產出合約 |
| 訪談者的開場 | `examples/shop/harness/act1/interviewer/prompt.txt` | 角色 + 那句原始需求 |
| 需求方的角色 | `.../act1/stakeholder/prompt.txt` | 不懂技術、只答被問到的、不准現編 |
| **需求方腦中的需求** | `.../act1/stakeholder/spec/SPEC.md` | **凍結的 `examples/shop/spec/SPEC.md`**,測試釘住逐位元組相同 |

**產出**:`transcript.md`(記 session 邊界)、`rounds/rN-{questions,answers}.md`(逐輪落地)、
`relay-ledger.jsonl`、`run-meta.json`(model + 輸入 blob)、`interviewer/SPEC-draft.md`。

**檢查**:`relay_ledger.verify` —— 每筆 answered 都要有對應的 relayed。
判準刻意寫得很笨,寫成「大致上都有轉交」的話 2026-08-18 那個洞就會被形式滿足。

⚠️ **帳本只查「轉交了沒」,不查「記到了沒」。** 「每個答案都指得出落點」這條判準寫在
產出合約 §11,但它**只在收尾查一次,而且是 agent 自己查自己** —— 漏了的東西
不會知道自己漏了。

**第二個檢查(票 05,2026-08-18 新增)**:`landing_check.py` —— 第 N 輪問出去的每個題號,
要出現在 `r(N+1)-questions.md` **開頭那張落點表**的某一列裡。判準一樣刻意寫笨:
落點表 = 該輪**提出新問題之前**的 markdown 表格資料列;散文寫一句「收到了 Q8 到 Q11
的回答」**不算**(那句話裡 Q9、Q10 一次都沒出現)。明確答「沒有」「還沒想過」的
**也算落點** —— 它們該進 §4 或未答追蹤,不是消失。

⚠️ 幾個上限**印在報表裡**,不是只寫在票裡:**題號出現 ≠ 記對了**(抓得到「整題消失」,
抓不到「記成別的意思」);**最後一輪是「不適用」不是「通過」**,自成一類印在最上面
(ADR 0005 §6)。`SPEC-draft.md` §11 那張收尾表只印成參考、**不進判定** ——
它是訪談者自己寫的,不能拿來把「不適用」補成「通過」。

⚠️ **2026-08-18 稽核後補的第三種不適用:「一題都沒認出來」。**
原本的守衛只擋「沒有成對的 rN/rN+1 檔」,擋不住「檔案成對、而題號一個都沒認出來」
—— 那一輪照樣算 compared、漏接 0,**整份綠燈**。實測:把一份 15 題的真實 run
只把題號寫法 `**Q1.` 改成 `**Q1:`(其他一字不動),就印出「可比對 3 輪 / 0 題;
通過 0、漏接 0」而 exit 0。**訪談者換個標點,守衛靜靜地不再適用而沒有人會發現。**
現在:一題都沒認出來的那一輪是**不適用**;粗體題號但認不出來的寫法(`**Qn:`)
會被單獨印成「題號寫法可能漂了」;一輪都比不了 = **整份不適用**。
離開碼因此跟另外兩支報表對齊:

| 離開碼 | `landing_check` | `contract_triage` / `glossary_check` | `provenance_check` | `acceptance_gwt` |
|---|---|---|---|---|
| 0 | 可比對的輪都通過了 | 沒有待處理項目 | 掃到了東西(**佇列不是判決**) | 全部通過 |
| 1 | 有漏接,或「掃到卻掃錯」(題號沒認出來 / 寫法漂了 / 輪次斷號) | 有分診項目 | —(沒有這個碼) | 有項目未通過 |
| 2 | 用法錯誤(吃錯目錄) | 用法錯誤 | 用法錯誤(吃錯目錄) | 用法錯誤 |
| 3 | **整份不適用**(一輪都比不了) | **不適用**(契約 / 詞彙表 0 條) | **整份不適用**(一筆都沒掃到) | **有項目不適用**(⚠️ 部分,不是整份) |

`provenance_check` 與 `acceptance_gwt` 這兩欄是 2026-08-24 補的(原本沒對齊)。
⚠️ `acceptance_gwt` 的 3 粒度不同:三段裡任何一段 ⏭️ 就回 3,不是「整份」。

(`landing_check` 的「只有答案檔的舊 run」從 exit 1 改成 **exit 3** —— 那是整份不適用,
不是「有漏接」。05-PREDICTION 對那份只釘了「exit ≠ 0」,凍結的預測沒有被動到。)

> ⚠️ **這一幕曾經每次跑都丟掉最後一輪**(迴圈 off-by-one,最後一次的
> `message = answers` 是死碼)。修法是 `final_message()` 把最後一輪的答案帶進收尾指示
> —— 轉交與收尾成為同一則訊息,結構上不可能再漏。

**驗過沒有**:
- ✅ 帳本邏輯:對 2026-08-18 的**真實逐字稿**重建帳本,`verify` 直接點名第 4 輪沒轉交
- ✅ 真跑:**haiku × 2 輪與 × 4 輪各一次**,四輪全部轉交,四份輸入到位
  (`runs/2026-08-18-act1-haiku-roleplay/`)
- ✅ `landing_check` 對**四份真實 run** 驗:opus-rerun 15 題全有落點(0 漏接)、
  haiku roleplay **漏掉整整兩輪 8 題**(那兩輪的下一輪開頭連一張表都沒有)、
  smoke 第一輪 5 題全滅、只有答案檔的舊 run 印「無法檢查」而非綠燈(exit 3)。
  另外釘住「題號寫法漂掉的 run 不算通過」:opus 那份改成 `**Qn:` 之後 exit 3,
  20 個近似寫法逐輪印出來 —— 而近似偵測在四份真實語料上**一次都不吵**。
  **同一支既印得出 0 也印得出 8** —— 而這三份的 `relay_ledger.verify` 都是綠的:
  **轉交了 ≠ 記下來了**
- ✅ **考卷:5 case**(票 25,`fixtures/exams/landing_check/`,`python3 exam.py` 跑、
  `test_exam.py` 每 case 一支)—— clean(0)/ `**Q1:` 寫法漂掉(3)/ 漏兩輪 8 題(1)/
  只有答案檔的舊 run(3)/ 吃錯目錄(2),離開碼與報表字串都釘;片段抽自上面那幾份真實 run。
  改了這支之後有東西會自動再比一次;**考卷抓得到壞掉的閘門,突變驗過**(`25-RESULT.md`)
- ✅ **真人需求方那一跑(2026-08-19,`runs/2026-08-19-act1-human-stakeholder/`)**:
  需求方是**真人(Nat)**、訪談者是 bare dir 裡的 subagent,六輪 30 題 →
  42,601 B 的 `SPEC-draft.md`,帳本六輪 asked/answered/relayed 全成對。
  ⚠️ **兩個理由讓它不能拿來抵下面那條**:需求方不是 agent(`run-meta.json` 寫著
  「不得與 agent-stakeholder 的跑直接比較基線」),而且**刻意不給訪談者
  `act1/interviewer/prompt.txt`**(那份會白送需求方身分 / 沒有既有系統 /
  沒有架構模板文件三樣情報)—— 輸入面本來就不同
- ❌ **opus 沒跑過** —— 修好的 orchestrator + 分家後的 prompt,還沒用正式模型驗
  (8/19 那跑的訪談者在 `run-meta.json` 裡記的是 `claude (subagent, bare dir)`,不是 opus)

---

## 幕二:落檔

```bash
tools/harness/run_act2.sh <散文規格.md> <工作目錄> [model]       # 開頭查幕一的帳本(票 21);ACT2_DRY_RUN=1 只組目錄
python3 tools/harness/check.py spec_store import <工作目錄>/{acceptance,glossary,contracts}.yaml <工作目錄>/spec.db
python3 tools/harness/check.py --run-dir <工作目錄> provenance_check <幕一 run_dir> <散文規格.md>
#   ↑ provenance_check 的目錄參數是幕一的 run,推不到幕二 → --run-dir 明給,帳本才會落在 run_act3.sh 讀的地方
```

隔離是刻意的:agent 只拿到散文規格 + `schema.sql` + `spec_store.py`。
**生成器、驗收 harness、既有的 acceptance.yaml 都不在裡面** —— 那些是答案卷。
它的完成定義是「`import` 印 ok」,一個它自己跑得動的迴圈。

**檢查三層**(不要混;2026-08-25 之前是兩層,票 23 補了第 0 階):

| 層 | 誰擋 | 例 |
|---|---|---|
| 第 0 階 | `spec_store.py` 的佔位符守衛(`check_placeholders`,在 schema **之前**跑) | 整格是 `TODO` / `[待補]` / `<customer id>` / `???` / `""` 的匯不進去,逐格印路徑;`[Q7] …` 引用與句中的 TODO 放行(判準是「整格只有」不是「含有」);**只有空白 `"   "` 不歸這階**,歸第 1 階 |
| 第 1 階 | `schema.sql` 的 CHECK / FK / TRIGGER | 五格來源標記寫不進第六格;違法 fixture 只掛得上預期被拒的情境;空白格(`length(trim(x)) > 0`,**⚠️ 不是每欄都有**:`acceptance_scenario.id` / `proxy_for` 驗過是缺口,見票 23 RESULT) |
| 第 2 階 | `spec_store.py` 的跨列不變式 | 總額 ≠ Σ(數量×單價) 匯不進去;拒絕情境的客人不得借用成功情境的 |

⚠️ **`spec_store.py` 是幕二 agent 拿得到的輸入。2026-08-25 起 `import` 有第 0 階,之後的第二幕跑
不得與之前的比基線**(`run-meta.json` 記著輸入 blob,比之前先看那個)。第 0 階對既有三份真實 yaml
(`2026-08-18-act2-opus` / `2026-08-18-act2-rerun` / `2026-08-19-act2`)**零命中,離開碼與訊息
逐字不變**(驗過,`.scratch/ddd-harness/23-RESULT.md`),所以那三跑的紀錄本身沒有被改變意義。

**加上第三個檢查(2026-08-18 新增)**:`provenance_check.py` —— 宣稱出自需求方的具體值,
他真的說過嗎。**分診佇列不是判決**,抓得到「訪談者餵值再標成親口確認」,
抓不到「需求方自己編」(那要靠票 04)與單位換算。

**再加兩支分診(2026-08-18,ADR 0005 / 票 06-A、08-A)**:

```bash
python3 tools/harness/check.py contract_triage <spec.db>   # 微尺度:§3 領域契約
python3 tools/harness/check.py glossary_check  <spec.db>   # 詞彙:§1 詞彙表 ↔ 對外欄位名
# 兩支的離開碼閘門不看(佇列不是判決),只要求跑過;帳本落在 <spec.db> 所在目錄
```

兩支都**不生成任何可執行的東西**,買的是分診;兩個對應的頂層區塊
(`domain_contracts` / `glossary_terms`)都是**選填**,所以兩支都綁死一條:
**「不適用」不算「通過」**,自成一類、印在最上面、離開碼 3。

- `contract_triage`:「有指名測試」與「由誰強制」**分兩段印,不合併計數** ——
  合併就把 invariant → example 的降級蓋掉。
- `glossary_check`:對譯檢查是**第 2 階報告不是 FK**(硬擋拿不到「差幾個」)。
  它**不掃任何識別字、不看任何類別名** —— 那是票 08-B,未決。

**驗過沒有(2026-08-18,對三份真實語料)**:

| 語料 | 詞彙表 | 對外合約 | 結果 |
|---|---|---|---|
| 凍結那份 | `spec/GLOSSARY.md`(15 詞) | `harness/acceptance.yaml` | 列表 5 欄 **對不到 4**;唯一對得到的是**撞名**不是對譯 |
| 第二幕那份 | `act2-from-interview/input-SPEC.md`(11 詞) | `act2-rerun/agent-acceptance.yaml` | 列表 7 欄 **一個都對不到** |
| 本輪訪談那份 | `act1-opus-rerun/SPEC-draft.md`(17 詞,**唯一有「對外欄位名」欄的**) | **不存在** | **不適用**(不是通過)—— 情境一份都沒落檔,不跨 run 硬配 |

⚠️ 第二幕那組的 0/7 **比手算的答案難看**(手算說 4 個對得到)。差在哪:那 4 個是人在
腦裡做的翻譯,**規格裡沒有任何一格記著**。落檔 agent 把完整的對譯寫在 yaml 的**註解**
裡 —— **做對了,而且沒有留下任何機器看得見的痕跡。** 這正是票 08 要抓的東西:
自律換個模型就沒了,而且連「上一個模型做對了」都證明不了。

- ✅ **考卷:`contract_triage` 4 case、`glossary_check` 6 case**(票 25,`fixtures/exams/`)——
  兩支都釘 clean(0)/ 已知陽性(1:凍結那組的「5 欄對不到 4、唯一對得到的是撞名」;
  訪談那份的 C12 跨聚合根 + 指不出測試)/ 兩種不適用(3)/ 吃錯目錄(2)。
  ⚠️ 兩支的 clean 是**合成**的:真實語料裡沒有一份對譯 0 差額、或契約全部指得到測試。

**驗過沒有**:
- ✅ agent 交得出可用的結構化 spec,判定完全機械(`runs/2026-08-18-act2-opus/`)
- ✅ 訪談產出的規格:**落檔 4/12 → 12/12,真實覆蓋 3 → 8**(`runs/2026-08-18-act2-rerun/`)
- ✅ `provenance_check` 抓到已知陽性(opus 那場的 100/120),0 假陽性
- ✅ **考卷:`provenance_check` 5 case**(票 25)—— 100/120 那個形狀 B(0 + 兩個值都印)/
  clean(0)/ 一筆都沒掃到(3)/ 吃錯目錄(2)/ **票 03 reopened 的三筆已知假陽性釘成
  「今天會印」**(推導值 120、`YYYY-MM-DD`、`QUANTITY_OUT_OF_RANGE`):票 03 修好那天這個
  case 會翻紅,到時改 expected,不是靜靜地過
- ✅ **真人訪談那份規格首次落檔(2026-08-19,`runs/2026-08-19-act2/RESULT.md`)** ——
  Opus,21 turns / 15.2 分 / $6.21,三份 yaml 都交:**17 條 GWT → 5 條情境**、
  17 條契約 `no_named_test_reason` **17/17 非空**、31 個詞落檔(14 個宣告對外欄位名)。
  ⚠️ 這是 `run_act2.sh` 改成「交三份 yaml」、且 `schema.sql` / `spec_store.py` 剛清過洩題
  之後的**首跑**,**不得與 8/18 那幾跑比基線**
- ❌ **主發現是壞消息:它三次都選擇誠實,而三次都寫在存不下來的地方。**
  補幣別欄、拿客人姓名當 `customer_id`、金額單位是「元」卻填進 `unit_price_cents`
  —— 三次都在 **YAML 註解**裡寫明,而**註解在 `spec_store.py` 解析時被丟掉**。
  跟票 08 量到的一模一樣:**同一種失效,換一個位置又發生一次**(票 15)

---

## 幕三:生成

```bash
tools/harness/run_act3.sh <spec.db> <out>          # 開頭查幕二的帳本(票 21),再跑下面兩支生成器;任一不適用 → 3
python3 tools/harness/gen_archunit.py   <spec.db> <out>/ArchitectureTest.java      # ⚠️ 直接跑生成器繞得過閘門 ——
python3 tools/harness/gen_acceptance.py <spec.db> <out>/OrderAcceptanceTest.java   #    閘門只在 run_act3.sh(test_harness.py 直接呼叫兩支的 main(),本體不動)
python3 tools/harness/check.py verify_generated <generated_dir> <spec1.yaml> [<spec2.yaml> …]
```

`gen_acceptance` 生**兩個** class:

- `OrderAcceptanceTest` —— 真情境。**全綠 = 驗收通過**
- `OrderProxyAcceptanceTest` —— 代理編碼的情境。**全綠不代表那些條文成立**
  (fixture 不含它宣稱的動作)。**這個 class 的大小就是缺口的大小**,補上動詞後它會變空

**wire shape 歸規格擁有**(ADR 0004):欄位名從 `wire_contract` 表來,生成器兩側都讀它,
不再寫死。沒宣告就不生 —— 猜出來的名字跟實作全對不上,而紅的原因看不出是命名。

**驗過沒有**:
- ✅ 兩個生成器都有驗收;drift check 蓋到全部三個生成物
- ✅ **生成物真的沒被下游動過**(2026-08-19):幕四跑完之後,工作目錄裡那三支測試檔
  對 `runs/2026-08-19-act3/` 的產出 / 骨架**逐位元組相同**(`runs/2026-08-19-act4/RESULT.md`)
- ⚠️ **drift check 的兩個已知盲區**:生成器**不適用**時那些檔案這一次沒有被檢查過
  (自成一類印在最上面,離開碼 3;不適用而 commit 裡有那個檔 = 異常,1 蓋過 3);
  以及 `GENERATORS` 是白名單、不掃目錄,**沒有任何生成器認領的 `.java` 對它完全隱形**

---

## 幕四:實作 ⚠️ 2026-08-19 跑通了一次,而「全綠」只證明了 1 條真情境

```bash
python3 tools/harness/check.py --run-dir <骨架目錄> acceptance_gwt <generated>/OrderAcceptanceTest.java <workdir>
#   ↑ 先跑這個:run_act4.sh 的閘門讀**骨架目錄**的帳本,要一筆 exit 0(workdir 跑之前可能不存在,推不到 → 明給)
tools/harness/run_act4.sh <散文規格.md> <骨架目錄> <工作目錄> [model]
ACT4_DRY_RUN=1 tools/harness/run_act4.sh …   # 只組工作目錄,不呼叫 claude(不花錢);閘門一樣要過
ACT_GATE_SKIP=1 ACT_GATE_SKIP_REASON='…' tools/harness/run_act4.sh …   # 逃生口,理由寫進 run-meta.json

python3 tools/harness/check.py vacuous_tests …   # 假驗收分診(PIT + 支配關係);不擋任何下游
```

⚠️ **這道閘門在本 repo 目前過不了,只能跳**(見開頭〈幕與幕之間的閘門〉的驗證):`acceptance_gwt`
第一段要 `git archive 4567d31`,那個物件沒跟著從 `kc-log` 搬過來;而且它對非凍結合約的 spec
一定回 3。**跳的時候理由要寫這個**,不要寫別的。

隔離同幕二:bare dir,只有**散文規格 + 骨架**。生成器、spec store、凍結的
`examples/shop/app/` 都不在裡面。工作契約寫死在 runner 的 heredoc(**受測品**,
每跑留 `prompt.txt`,寫報告前 diff),原料是散文自己的〈不得開工的部分〉與
〈完成的定義〉兩節,方法論來自 `docs/adr/0006`。

**工作契約的六條**(ADR 0006 → prompt):

| | 寫死了什麼 |
|---|---|
| 完成的定義 | `./gradlew test` 全綠,而它**按 class 名只跑生成的那三個** |
| 內圈測試 | 住 `src/innerTest/java`,`./gradlew innerTest` 跑,**不算進全綠** |
| seam | 查散文〈契約〉表的「守在哪個聚合根內」欄,**不問人**(隔離跑沒有人可問) |
| 做法 | outside-in,一次一條 vertical slice;refactor 不屬於迴圈 |
| 恆真 | `tautological` 的定義逐字寫進去,期望值只能來自規格/字面值/算過的例子 |
| 留白 | 〈不得開工的部分〉三條逐條搬;歧義自決 → `ASSUMPTIONS.md` |

⚠️ **結構隔離不是防竄改。** 工作目錄裡的 `build.gradle` 可寫,agent 刪掉那段
filter 它的測試就回到 `test` 裡。runner 在注入之後算雜湊基線,跑完再算一次,
落 `tamper-check.txt` —— **擋不住,只查得出來**。其餘已知上限見 `run_act4.sh` 檔頭。

**雜湊證不了「測試先於實作存在」**(票 24,2026-08-25)。那條原本只靠幕三 → 幕四的
構造順序保證。⚠️ 直接抄 ai-harness-template 的 `check-test-first.sh`(比測試檔與 source
檔的首次 commit 時間)會抄到一支**永遠不會響**的檢查:工作目錄是 bare dir,產物一次 commit
進主 repo,兩者的首次 commit 永遠是同一個。所以 runner 現在在 `prompt.txt` 寫完、呼叫
claude **之前**,讓工作目錄自己 commit 一版基線(歷史放 `harness/act4.git`,**刻意不放
`.git`** —— git 2.54 實測,run 目錄帶 `.git` 會被主 repo 記成 gitlink,run 的檔案一個都
進不了主 repo);跑完再 commit 一版,`act4_order_check.py` 比「`src/test/**` 全在基線裡、
`src/main/**` 扣掉受保護 wiring 與 `.gitkeep` 全在基線之後」,落 `order-check.txt`,
基線 hash 另記進 `run-meta.json`。三態:**0** 過 / **1** 任一測試檔不在基線、任一實作檔在
基線裡、歷史與 `run-meta.json` 對不上、有紀錄說做過基線但歷史不見了 / **3 不適用**:沒有
`harness/act4.git` 也沒有紀錄(舊 run)—— **不折成通過**,印在最上面。跟雜湊同一種性質:
agent 對 `harness/act4.git` 做 `--amend`、改寫歷史、連 `run-meta.json` 一起刪,就過或回 3
—— 上限印在報表裡。⚠️ `ACT4_DRY_RUN=1` 也做基線 + 檢查(不花錢,測得到)。
**驗過的**:對 `runs/2026-08-19-act4/` 跑 → 3;dry run 重組 → 0,`run-meta.json` 的
`baseline_commit` = root commit;用 stub `claude` 走完跑完那段(commit → 檢查 → repack)→ 0,
歸檔形狀重跑仍 0;合成三態 14 條 pytest(`test_act4_order.py`,`.scratch/ddd-harness/24-RESULT.md`)。
**沒驗過的**:真的 claude 跑一次 —— agent 的環境從此多了 `harness/act4.git`,
跟 2026-08-19 那跑不完全同環境;agent 自己 `git commit` 不會進這份歷史,檢查分不出它內部的先後。

**內圈測試的落點檢查 + 恆真分診**(票 13,2026-08-25;兩個都不是判決):

```bash
python3 tools/harness/innertest_landing_check.py <spec.db> <workdir>   # 契約 → 內圈測試落點,三段分開印
```

契約 → 內圈測試這層以前只有 prompt 裡一句「方法名要帶契約編號」,沒有東西在讀。現在宣告改在
**測試檔頭**:`src/innerTest/**/*.java` 每支 class 的 javadoc 帶 `@covers C8, C9`(契約編號)或
`@covers G16`(情境編號;**編號從 store 讀,不寫死前綴** —— 2026-08-19 那份的情境是 G 不是 S),
一支檔可掛多條。三段:(1) **落點** —— 每條契約有沒有內圈測試 `@covers` 它,**契約決定離開碼**,
情境只印參考(它們的落點是幕三生成的驗收);(2) **反向** —— 每個 `@covers` 指到的編號 store 裡
存不存在,指了不存在的 = 漂;(3) **打在哪個入口** —— 印 `第 4 階,人讀`,列 `Type.method(` /
`new Type(` / `Type.class` 三種 token,**不判斷**。舊約定(方法名帶編號)**不算落點**,只計數。
離開碼:**0** 每條契約有落點且沒有漂 / **1** 任一契約無落點或任一宣告漂(**目錄在但零個檔、零個
`@covers` 也是 1** —— runner 自己會 mkdir 那層,空的正是 agent 什麼都沒寫的長相)/ **2** 用法錯誤 /
**3 不適用**:沒有 `src/innerTest/` 目錄,或 store 契約與情境都 0 條。恆真分診(副)**不在這支裡跑**,
仍交 `vacuous_tests`;第三類「範圍不足」(票 13 陽性一)**兩支都抓不到**,印成固定提醒。
heredoc 第四節加了一句「檔頭必須 `@covers C<n>` / `@covers S<n>`」(`prompt.txt` blob
`d4a17c9a` → `c4444978`,diff 只有那一段;舊的「方法名帶編號」那句**留著**,兩種約定並存)。
**驗過的**(`.scratch/ddd-harness/13-RESULT.md`):對 `runs/2026-08-19-act4/` 跑 → **1**,契約
17/17 無落點、舊約定 9 條、`OrderImmutabilityTest` 那格列出 `Order.class`;考卷 5 case(clean 0 /
舊約定無落點 1,片段抽自那跑的 `MoneyTest.java` / 不適用 3 / 漂 1 / 用法錯誤 2)全命中;
16 條 pytest(`test_innertest_landing.py`)。在 scratchpad 複本上加 PIT 跑 `vacuous_tests`:
71 mutant、佇列 5/9,**陽性一不在佇列、陽性二的 C9 / C17 在佇列** —— 但它們進佇列是因為兩條殺的
是同一組 7 個 mutant(互相支配,`vacuous_tests` 檔頭的 (b) 重複),不是恆真;`RECEIVED -> null`
那個漏 PIT 沒生 mutant(`OrderStatus.java` 0 個);`Order.restore` 是 NO_COVERAGE(陽性一的
「範圍不足」PIT 資料裡有,`vacuous_tests` 只看測試所以沒印)。
**沒驗過的**:真的 claude 照新 prompt 跑一次(要錢);`@covers` 這條約定是否會被形式滿足(上限印在報表)。

`acceptance_gwt` 三段,**三態**(過 / 沒過 / **不適用**):

1. **空骨架 → 全紅** —— 證明驗收不是恆真。與被測規格是哪份無關,**永遠適用**
2. **可滿足性** —— 只有宣告 `shop-frozen-v1` 合約的 spec 才拿 OL1 當綠燈預言機;
   其他 spec 印 `⏭️ 不適用`,**可滿足性要由這一幕自己證明**
3. **逐條可紅** —— `BREAKS` 綁凍結那份的情境語意,換 spec 會撞名不撞義 → 不適用

> ⚠️ 報表印得出「不適用」是刻意的。舊版對不同合約印 `❌ 0/4 綠`,讀起來像壞了
> —— **而壞掉的東西會被拿去修**。結論句會講「跑到的都通過,但有 N 項不適用,
> **這不等於驗收通過**」。

**驗過沒有**:
- ✅ 空骨架全紅(凍結那份 5/5、訪談那份 12/12、分 class 後 8/8)
- ✅ 凍結合約的迴歸網 **7/7**(空骨架全紅 + OL1 全綠 + 逐條可紅 5 條)
- ✅ 結構隔離(2026-08-19,票 12)用**兩個誘餌**實測:`src/innerTest/` 那支不跟
  `test` 跑;塞進 `src/test/java/acceptance/` 的 `SneakyTest` **也不跟 `test` 跑**
  —— `test` 只產出那三支的 XML。注入之後外圈數字不變(12/12 紅、架構 4/4「不適用」)
- ✅ **管線閉環了(2026-08-19,第一次)** —— Opus,38 turns / 14.4 分 / $6.32:
  一句話 → 30 題 → 550 行規格 → 5 條情境 → **9/9 全綠 + 23 個實作 class**
  (`runs/2026-08-19-act4/RESULT.md`;輸入是 `runs/2026-08-19-act1-human-stakeholder/SPEC-draft.md`
  + `runs/2026-08-19-act4-skeleton`)。四項獨立查核都過:三支測試檔對 act3 產出**逐位元組相同**、
  受保護檔的雜湊沒被動、架構那 4 綠**不是空的**(domain 10 / usecase 5 / adapter 12 個 class)、
  `test` 按 class 名只跑那三支(內圈的 9 條沒被算進完成的定義)。
  `run_act4.sh` 的三樣設計(結構隔離內圈、雜湊防竄改、seam 由契約表指定)在真實資料上都生效。

  ⚠️ **以下四條但書一條都不能省 —— 「跑通了」不等於「驗過了」:**

  1. **「全綠」只證明了 1 條真情境。** 9 綠裡只有 G16 出自 `OrderAcceptanceTest`;
     另外 4 條住 `OrderProxyAcceptanceTest`(代理編碼,fixture 不含它宣稱的動作)、
     **不算驗收**,再 4 條是 ArchUnit。**一個只讓 G16 過的實作也會全綠** ——
     這次它做得多得多,但那是這個模型的行為,不是驗收逼出來的。
  2. **17 條 GWT 只有 1 條、17 條契約只有 8 條走到了實作面前。** 契約掉的九條全是
     跨聚合根 / 結帳 / 付款 / 庫存那一組 —— **在第二幕就落不了檔**,不是實作偷懶。
  3. **架構那 4 條是凍結骨架繼承來的,不是這份規格生的。** 這份規格 §9 的 10 條
     **一條都沒落檔**(票 16)—— 那 4 綠證得了實作沒違反骨架帶來的規則,
     證不了這份規格自己的架構主張。
  4. **只有一份實作。** MISSION 要的「兩個模型的實作都被同一套驗收判定」還沒做到。

  ⚠️ 這一跑的主發現是壞消息:**規格與它自己的驗收互相打架,而規格輸了。**
  對外合約被驗收改寫四處(`{"orders":[…]}` → 裸陣列、ISO-8601 帶時區 → `yyyy-MM-dd`、
  兩階段 `{checkoutId,paymentId}` → 單階段、客戶三欄 → 一個字串)。實作 agent
  **自己發現、自己寫進 `ASSUMPTIONS.md`**,而那條鏈**在第二幕就斷了,
  斷的那一刻沒有任何機械檢查在看**(票 15 最強的證據)。

---

## 幕五:review(洞 → 搬階 → 改 harness)

MISSION 說這是 **harness 唯一會複利的地方**:
「agent 犯了錯 → 錯誤被轉成 pattern 或驗收條目 → 同類錯誤不再發生」。

**閉環的定義**:改完之後**重跑並量到差異**。改了但沒重跑 = 沒閉環。

**驗過沒有**:
- ✅ 第二幕那半:負面情境落不了檔 → 改 schema → 重跑量到 4/12 → 12/12
- ❌ 第一幕那半:off-by-one 修了、帳本做了、prompt 分家了,**opus 沒重跑過**
- ❌ 第四幕那半:2026-08-19 那跑挖出兩個洞(票 15 誠實過不了 store 那道邊界、
  票 16 第二幕的 prompt 不問架構規則),**harness 還沒改,更沒重跑** —— 依上面那條
  定義,這一幕在幕四這條線上**還沒閉環過**

---

## 現在缺的(原本三塊,2026-08-19 剩一塊半)

1. **opus 跑一次幕一** ~$10–20 —— 幕一的 agent-需求方那條線,修復後仍只有 haiku 的證據。
   8/19 那跑的需求方是**真人**、訪談者是 bare-dir subagent,**不能拿來抵**(見幕一)
2. ~~**骨架**~~ —— **已做**(票 10,`examples/shop/app-from-interview/`,空骨架 12/12 紅)
3. ~~**幕四跑一次**~~ —— **已做**(2026-08-19,`runs/2026-08-19-act4/`,9/9 全綠)。
   **但剩半塊**:MISSION 要的是「兩個模型的實作都被同一套驗收判定」,現在只有一份實作;
   而且這一跑的驗收只逼出 1 條真情境(四條但書見幕四)

## 停損規則(2026-08-18 訂)

**票 03 是付費跑之前的最後一次改動。** 票 04 的方向、票 02 做不做、
wire shape 措辭,**全部等 opus 那跑的資料再決定**。

那一跑本身是收斂測試,預先登記「不會冒出新的失效家族」,而
**新家族 = 現有的票與 FINDING 都涵蓋不到、必須開一張新票**(判準是機械的)。

## 開著的票

`.scratch/ddd-harness/issues/` —— **共 31 張,16 張已完成**(更新 2026-08-25;21–27 是 survey §9 的落地,見 ADR 0007 / 0008)。

**已完成**:05 答案落點檢查(`landing_check.py`)/ 06-A 契約進 store(`domain_contract` +
`contract_triage.py`)/ 08-A 詞彙進 store(`glossary_term` + `glossary_check.py`)/
09 幕四方法論(→ `docs/adr/0006`)/ 10 骨架(`examples/shop/app-from-interview/`)/
11 package 落點檢查(`package_landing_check.py`)/ 12 幕四 runner(`run_act4.sh`)/
14 兩個檢查缺陷 / 16 第二幕加交架構規則 / 18 本檔與 README 對齊現況 /
21 幕間閘門 + 檢查帳本(`check.py`、`run_act3.sh`、三支 runner 開頭)。
25 檢查器考卷(`exam.py` + `fixtures/exams/`,20 case;`package_landing_check` 仍在無考卷佇列)。

**要 grill 才動得了**(形狀未定,動 schema 或動受測品):
- **01** 動詞不夠 —— step 只表達得了「送出一筆訂單」。**卡著 06-B/C**
- **02 + 15** —— 併場。02 是「不誠實時抓不抓得到」,15 是「誠實時有沒有地方寫」,
  兩張共用 `proxy_for` 這個物件。⚠️ 02 的解 blocked 條件(不同密度的第二個樣本)
  **2026-08-19 那跑可能已滿足**(4 個 `proxy_for`,成因是新的一種:「概念不存在」而非
  「動作不存在」),但只滿足清單第一項
- **13** 內圈落點 + 恆真分診 —— blocked 的前提已滿足(有 9 條真的內圈測試 + **兩個已知陽性**),
  但形狀因那兩個陽性而變了(多了第三類病:**範圍不足**,落點檢查與恆真分診都抓不到)

**要當面拍板的取捨**:03 來源標記(第二份規格上精確度 0%,已 reopened)/ 04 需求方 agent
算不算儀器 / 07 Event Storming 要不要進訪談 prompt(動受測品)/ 08-B 實作層命名要不要驗

**還開著的工**:17 第 10 課重寫(**已完成**,`lessons/0010-*.html`)

