# 22 — `CLAUDE.md` 的票規約一條都沒有 lint:Status 漂、票號計數錯、PREDICTION 先後沒人查

**What to build:** `tools/harness/harness_lint.py`,對 `.scratch/ddd-harness/` 與 `docs/adr/` 跑,
第一批規則見下;進 pytest。

**Blocked by:** None(ADR 0007 已 accepted)

**Status:** needs-triage —— 2026-08-25 Nat 拍板要做(survey §9 #2,ADR 0007 的落地),尚未開工。

## 哪裡壞了

`CLAUDE.md`〈票怎麼開、怎麼關〉寫了規約,並自承 Status「漂得很兇」;票號計數寫「到 18」時
實際到 20(2026-08-25 才修)。`NN-PREDICTION.md` 要在跑之前寫 —— 是這個 repo 量儀器準不準的
唯一方式 —— 而「之前」沒人查。run 目錄被票引用就不能刪,靠人記得 `grep`。

對照(驗過,survey §3 第 12 條):Agentheim `lib/human-eye-criteria.mjs` / `spike-stop-loss.mjs` /
`duplicate-id-check.mjs`,全部 stdlib、side-effect-free、loss-tolerant(讀不到就不標)、
有 `ADOPTION_DATE` 祖父條款。**照這個形狀寫。**

## 第一批規則

| 規則名 | 查什麼 | 資料來源 | 祖父 |
|---|---|---|---|
| `ticket-filename` | `NN-kebab-slug.md`,NN 兩位數且不重號 | 檔名 | 否(既有全合) |
| `status-vocabulary` | `**Status:**` 第一個詞在 {needs-triage, needs-info, blocked, reopened, done, resolved, A 半 done};**新票只准前六個**(`resolved` / `A 半 done` 只給祖父) | 票第一個 `**Status:**` 行 | 是 |
| `status-single-cell` | 只有一個 `**Status:**` 行(整格重寫,不追加) | 票 | 是 |
| `prediction-before-result` | `NN-RESULT.md` 存在時,`NN-PREDICTION.md` 的 **git 首次 commit** 不晚於 RESULT 的 | `git log --diff-filter=A --format=%ct` | 否 |
| `prediction-before-run` | 票內文引用的 `runs/<name>` 目錄,其 git 首次 commit 不早於對應 `NN-PREDICTION.md` 的(抓不到「先跑再補預測但一起 commit」—— **印在報表上限**) | git | 是 |
| `referenced-run-exists` | 票內文出現的每個 `runs/<name>`,在 `examples/**/runs/` 找得到 | 檔案系統 | 否 |
| `blocked-by-resolvable` | `**Blocked by:**` 提到的票號存在 | 票 | 是 |
| `convention-undecided` | ADR 0007 §4:祖父日之後的票含立規詞而無規則名 / 無 `prose-only, unenforced` → **佇列** | 票 | 是 |
| `ticket-count-in-docs` | `CLAUDE.md` / `PIPELINE.md` / `README.md` 寫的「N 張」等於實際張數 | 三份文件 | 否 |

`ADOPTION_DATE = 2026-08-25`,以檔案 git 首次 commit 日期判「新舊」,**不用 mtime**
(survey §3 第 3 條:fspec 用 mtime,`touch` 就過)。

## 離開碼

照 `PIPELINE.md` 那張表:0 沒有待處理項;1 有;2 用法錯;**3 不適用(一張票都沒掃到)**,
自成一類印最上面。`convention-undecided` 是佇列,單獨印,**不計入 1**(先量假陽性)。

## 慣例(ADR 0007)

本票立的規則全部由 `harness_lint` 自己守。表裡「祖父=否」的規則對既有資料要先全綠 —— 不綠就是
發現了真的漂,**寫進 `22-RESULT.md`,不要為了綠改規則**。

## 完成的定義

- `test_harness_lint.py`(新檔,不動 `test_harness.py`):每條規則一正一反的 fixture,
  在 `tools/harness/fixtures/lint/` 下;加一條「對真 repo 跑,祖父=否的規則零命中」。
- `22-PREDICTION.md` 在對真 repo 跑之前寫:預期 `status-vocabulary` 對舊票命中 ≥ 3(06、08 的 `A 半 done`、09 的 `resolved`)但被祖父豁免;`referenced-run-exists` 零命中;`ticket-count-in-docs` 在本票合併前命中 3 處。
- `CLAUDE.md`〈票怎麼開〉加一行:「規約由 `harness_lint.py` 守,規則名見票 22」。
