# ADR 0010 — Hub 用 `vendor.sh` 把 `harness/` copy 走、各自發展;不用 submodule

## Status

Accepted(2026-08-26)。**取代** ADR 0009 §5 的機制(submodule 引用)與上游 commit `6017911`
的 sparse-checkout 做法;0009 §5 的**理由**(開工 prompt 只有一份正本、hub 的 `AGENTS.md` 只指過來
不複製)不變,現在套在 hub 自己那份副本上。

## Context

2026-08-26 kc-hub 第一次把 harness 拿進去,要的是「拿走之後各自發展,不回流上游」。實際做的事
(票 32,驗過):拆 submodule → 手挑 keep-set → 攤平 `tools/harness/` 到 `harness/` → sed 28 個檔的
路徑 → `REPO = parents[2]` 改 `parent` → 砍 52 條讀 `examples/` 當 fixture 的測試(第一輪 grep 漏 4 條)
+ 砍綁死 `.scratch` 票的 `harness_lint`。每一步都是手工,下一個 hub(vpin-hub)再做一遍結果不會一樣。

根因兩個:可搬的那塊跟上游自己的東西(教材、`.scratch` 票、語料、票 lint)混在同一層;
`tools/harness/` 裡的 code 靠上層目錄(`parents[2]`、`../../examples`)。

## Decision

1. **上游重排成「`harness/` 一個目錄 = hub 拿走的全部」**:腳本、測試、prompt、`schema.sql`、
   `CONTEXT.md`、`CLAUDE.md`、`docs/adr/`、`README.md`、`hub-bootstrap.md`、`vendor.sh`、`test_vendor.py`。
   讀語料的測試搬到 `examples/shop/tests/`,票 lint 搬到 `tools/lint/`,兩者 hub 都不拿。
2. **Hub 用 `harness/vendor.sh <hub>` 拿**:copy `harness/` → `<hub>/harness/`,寫 `ORIGIN.md`
   (上游 commit、日期),在副本跑 pytest。不覆蓋已存在的。搬進去之後那份是 hub 的東西,
   跟 hub 一起 commit;**沒有任何東西流回上游**,要撿上游的改動就拿 `ORIGIN.md` 的 commit 手動 diff。
3. **`harness/` 裡不引用上層目錄**。

### 否決的

| 做法 | 為什麼不 |
|---|---|
| submodule(ADR 0009 §5) | hub 改一行要回上游 commit;兩個 hub 共用一個上游,一邊的改動污染另一邊;「各自發展」做不到 |
| sparse-checkout submodule(`6017911`) | 還是 submodule,上面三條一條都沒解;它只解決樹太大 |
| 寫 vendor script 去砍測試、改路徑 | 要維護一份「哪些測試依賴 `examples/`」的清單,上游一加測試清單就漂(第一輪就漏了 4 條)。所以改成上游自己重排,讓 `harness/` 本身乾淨,script 只做 copy |

## 由誰強制(ADR 0007)

| 項 | 守法 |
|---|---|
| 「hub 用 `vendor.sh` 搬,不用 submodule」 | `vendor.sh` + `test_vendor.py`:對 tmp dir 跑一次,副本 pytest 綠、`ORIGIN.md` 有 hash、`diff -r` 只差 `ORIGIN.md` |
| 「`harness/` 裡不引用上層目錄」 | **prose-only, unenforced**(票 32):`grep -rn 'parents\[' harness/` 加 `grep -rn '\.\./\.\./' harness/` 兩條 lint 就守得住,但先看有沒有第二次踩到再說 |

## Consequences

- **上游修正不會自動到 hub**;hub 之間會分岔。這是接受的,而且是目的:hub 要的就是各自發展。
- `ORIGIN.md` 是 hub 那份跟上游之間**唯一的錨點**:少了它就不知道從哪個 commit 開始 diff。
- `harness/CLAUDE.md` 要寫成 hub 中立(上游與副本逐字相同);只有上游才有的規約(票、`examples/`、
  教材)搬到根 `CLAUDE.md`。
- `run_act2.sh` / `run_act4.sh` 的 `NA_RATIO_ROOT` 預設改成 `$HARNESS/../runs`(hub 的 `runs/`);
  上游要掃語料自己傳 `NA_RATIO_ROOT=examples`。`run_act2.sh` 給 agent 的 sandbox 仍用 `$WORK/tools/harness/`,
  那是 sandbox 佈局不是 repo 佈局,不動。
- **沒驗過的**:vpin-hub 用 `vendor.sh` 拿一次是不是真的零手工。kc-hub 那份是用 script 重搬一次
  取代手工的(票 32 完成的定義),第一個 hub 不算第二個樣本。

相關:票 32(`.scratch/ddd-harness/issues/32-*.md`,預測在 `32-PREDICTION.md`)、ADR 0007(機械化)、ADR 0009 §5。
