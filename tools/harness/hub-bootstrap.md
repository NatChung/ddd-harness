# Hub 開工 prompt —— 把 harness 帶進 vpin-hub / kc-hub

> **這份是唯一正本,住 ddd-harness。** Hub 以 submodule 引用 ddd-harness,自己的 `AGENTS.md` /
> `CLAUDE.md` 只寫一句「harness 的用法讀 `harness/tools/harness/hub-bootstrap.md`」,**不複製本檔**。
> 理由:兩份散文講同一條規則會漂(ddd-harness `CLAUDE.md` 硬規則、ADR 0009 §5)。

## 你在哪、要做什麼

你在一個 **hub repo**(`vpin-hub` 或 `kc-hub`)。它不是 product repo,是工作區:
真正的 code 在 `codebases/<repo>/`(各自獨立 clone,hub 不追蹤),harness 在 `harness/`(submodule → ddd-harness)。
你要做的是 **brownfield 的五幕**:對一個 feature,從既有 code 抽候選表、訪談、落檔、(之後)生驗收、實作。

## 先讀(順序,不要跳)

1. `harness/CLAUDE.md` —— 硬規則。**在 hub 裡一樣適用**,特別是:生成物不手改、runs 不改、預測先寫。
2. `harness/tools/harness/PIPELINE.md` —— 五幕、每幕的檢查、離開碼表、幕間閘門。
3. `harness/CONTEXT.md` —— 10 個詞。寫任何文件之前先讀,尤其「不適用↔通過」「代理編碼↔假驗收」。
4. `harness/docs/adr/0009-*.md` —— brownfield 的形狀:補充檔、第六格、幕零、提供方狀態、`[human-eye]`。
5. `harness/tools/harness/interview-brownfield.md` —— 訪談者會多讀的那份。
6. Hub 自己的 `AGENTS.md`(vpin-hub 有;kc-hub 照它的形狀寫)—— 誰負責哪個端、既有的交付規範(`doc-rules/`)。
   **harness 不取代那些,它接在前面**:五幕產出 spec 包,交付文件照 hub 既有規範寫。

## Hub 的目錄形狀

```
<hub>/
  harness/                 ← git submodule → github-NatChung:NatChung/ddd-harness
  codebases/<repo>/        ← product repo clone(hub 不追蹤;kc-hub 是 symlink → ../kc-knowledge/codebases)
  specs/<feature>/         ← 這個 feature 的 spec 包:act0-candidates.yaml、SPEC-draft.md、*.yaml、spec.db
  runs/<date>-<feature>-act<N>/   ← 每一幕一跑一目錄,run-meta.json 記輸入 blob;跑過就是歷史,不改
  tickets/                 ← hub 既有的票(vpin-hub 已有)
```

`specs/` 與 `runs/` **進 hub 的 git**;`codebases/` 不進。

## 第一次裝(每個 hub 一次)

```bash
git submodule add git@github-NatChung:NatChung/ddd-harness.git harness
git submodule update --init
pip install pytest pyyaml                      # 只這兩個
(cd harness/tools/harness && python3 -m pytest -q)   # 應全綠;紅了先停,回報
# kc-hub 專用:codebases 共用 kc-knowledge 的 clone 與 codegraph 索引
ln -s ../kc-knowledge/codebases codebases
```

codegraph:product repo 已有 `.codegraph/` 的直接用(`codegraph_explore` 帶 `projectPath`);沒有的**不要自己 init**,回報 Nat 決定。

## 五幕在 brownfield 怎麼走

| 幕 | 做什麼 | 指令 / 產出 | 檢查 |
|---|---|---|---|
| **零 抽候選** | 用 codegraph 抽**一片**(一個 Bounded Context),不是整個 app | `act0_extract.py codebases/<repo> <slice>` → `specs/<feature>/act0-candidates.yaml`(腳本落地前:手抽,形狀照 ADR 0009 §4 的表,每筆 `path:line`) | 沒有;prose-only。抽漏了靠訪談補 |
| **一 訪談** | 需求方是**真人**(PO / 營運);訪談者讀正本 + 補充檔 + 候選表 | template_dir 放 `interviewer/prompt.txt`(開場要提候選表、要說「有既有系統」)+ `interview-brownfield.md`;`orchestrate.py` 或真人轉述 | `check.py landing_check`、`relay_ledger.verify`;帳本寫進 run 目錄 |
| **二 落檔** | 散文 → yaml → `spec.db` | `run_act2.sh` → `check.py spec_store import`;第六格、`provider_status`、`human_eye` 寫得進 store 是 ADR 0009 落地票的事,**落地前這三樣先留在 yaml 註解並回報** | 三支分診 + `provenance_check`(洗白那條) |
| **三 生成** | **綁 Java。Dart / TS 生成器還沒有。** | 先手寫該語言的驗收測試,形狀照 `gen_acceptance.py` 的產物;`@covers` 檔頭約定照票 13 | `verify_generated` 不適用(沒生成器),照實印 |
| **四 實作** | 幕三手寫的情況下,幕四也是手動走:空骨架先全紅 → agent 填 | `run_act4.sh` 綁 gradle,**不能用**;照 ADR 0006 的六條寫該語言的工作契約 | 至少做到「空骨架全紅」有紀錄 |
| **五 review** | 洞 → 票 → 改 harness → 重跑 | 票開在 hub 的 `tickets/`;**改 harness 的票開回 ddd-harness** | — |

三、四兩幕**是移植的缺口**,第一個 feature 的目的就是量出「Dart / TS 那邊要什麼形狀」。
**不要為了走完五幕去硬湊生成器**;手寫、留紀錄、回報。

## 兩個 team + server 兩邊都參(KC)

- 一個 feature 一個 `spec.db`,Bounded Context 切 `app` / `web` / `server`,`wire_contract` 是三方碰頭的地方。
- 票的 frontmatter 標 `context: app | web | server`。
- 「等 server」分兩種(補充檔 §四):形狀定了 → `替身`,不擋;形狀沒定 → `形狀未定`,阻斷級,票標 `blocked —— 等 <誰> 定 <什麼>`。
- Scrum event 各開沒關係;**`spec.db` 是共同的正本,不是誰的 backlog**。

## 不准動的

- `codebases/` 底下任何檔(那是 team 的 repo;要改 code 走幕四,在**工作目錄**做,不在 clone 上)。
- product repo 自己的 `CLAUDE.md`(`/init` 產的,是 team 的)。
- `harness/`(submodule)—— 要改 harness 回 ddd-harness 開票。
- `runs/` 跑過的目錄。
- `interview-prompt.md` 正本(ADR 0008 blocked)。brownfield 差量只進補充檔。

## 每一幕結束要回報的

- 動了哪些檔(路徑清單)、`run-meta.json` 記了哪些 blob。
- 預測命中 / 落空 / 不適用各幾條(`specs/<feature>/<act>-PREDICTION.md` 與 `-RESULT.md`,跟 ddd-harness 的 `NN-PREDICTION.md` 同一個意思)。
- **「做了 ≠ 接上了 ≠ 驗過了」三欄分開講。** 指不出證據的寫「沒驗過」。
- 幕三、四手寫時:該語言缺什麼工具(ArchUnit / PIT 的對應物),寫成清單,那是生成器的需求。
