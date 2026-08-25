# 32 — harness 不是一塊搬得動的東西:hub 要拿它得手工挑檔、砍測試、改路徑

**What to build:** 上游重排成「`harness/` 一個目錄 = hub 拿走的全部」,加一支 `harness/vendor.sh <hub>` 做 copy + 寫 `ORIGIN.md`;
ADR 0010 記「hub 用搬檔案,不用 submodule / sparse-checkout」。

**Blocked by:** None

**Status:** needs-triage —— 2026-08-26 kc-hub 實搬一次量出來的洞;預測在 `32-PREDICTION.md`,寫在動手之前。

## 哪裡壞了

2026-08-26 kc-hub 要拿 harness 各自發展(不回流上游),實際做的事:拆 submodule → 手挑 keep-set(`tools/harness`、`CONTEXT.md`、`CLAUDE.md`、`docs/adr`)
→ 攤平 `tools/harness/` 到 `harness/` → sed 28 個檔的 `tools/harness/` → `harness/` → `REPO = parents[2]` 改 `parent`
→ 砍 52 條讀 `examples/` 當 fixture 的測試(第一輪 grep 漏 4 條)+ `harness_lint`(綁 `.scratch` 票)。
每一步都是手工,下一個 hub(vpin-hub)再來一遍結果不會一樣。`6017911` 改成 sparse-checkout 也沒解:還是 submodule,hub 改一行得回上游 commit,兩個 hub 互相污染。

根因:可搬的那塊跟上游自己的東西(教材、`.scratch` 票、語料、票 lint)混在同一層,而且 `tools/harness/` 裡的 code 靠上層目錄(`parents[2]`、`../../examples`)。

## 要改成

```
ddd-harness/
  harness/          ← 自足:腳本、測試、prompt、schema、CONTEXT.md、CLAUDE.md、docs/adr、README、hub-bootstrap.md、vendor.sh
  examples/shop/tests/   ← 讀語料的 52 條測試(從 tools/harness/test_*.py 搬出)
  tools/lint/       ← harness_lint(管 .scratch 票)
  CLAUDE.md         ← @harness/CLAUDE.md + 上游才有的段落(票規約、examples runs 不刪、教材慣例)
```

搬 = `harness/vendor.sh <hub>`:copy `harness/` → `<hub>/harness/`,寫 `ORIGIN.md`(上游 commit、日期),在副本跑 pytest。不覆蓋已存在的。

## 慣例(ADR 0007)

「hub 用 vendor.sh 搬,不用 submodule」—— 機械化:`vendor.sh` + `test_vendor.py`(對 tmp dir 跑一次:副本 pytest 綠、`ORIGIN.md` 有 hash、`diff -r` 只差 `ORIGIN.md`)。
「`harness/` 裡不准引用上層目錄」—— prose-only, unenforced:`grep -rn 'parents\[' harness/` 一條 lint 就守得住,但先看有沒有第二次踩到再說。

## 完成的定義

- 上游 `pytest`(`harness` + `examples/shop/tests` + `tools/lint`)= 457 + `test_vendor` 的條數,全綠。
- `harness/vendor.sh` 搬進 tmp hub,副本 `pytest` 綠,`grep -r tools/harness harness/` 只剩 `run_act2.sh` 的 sandbox 佈局。
- kc-hub 用 `vendor.sh` 重搬一次取代手工那份。
- `32-RESULT.md` 對答案。
