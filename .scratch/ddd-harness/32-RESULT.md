# 32 — 結果(對 `32-PREDICTION.md` 的答案)

日期:2026-08-26。重排 commit `25c131a`;kc-hub 用 `vendor.sh` 重搬:kc-hub 那邊的 commit 見它的 log。

| # | 預期 | 實際 | 判定 |
|---|---|---|---|
| **P1(釘)** | `pytest harness examples/shop/tests tools/lint` = 456 passed + 1 skipped(vendor 另計) | **465 passed + 1 skipped** = 456 + 1 + `test_vendor.py` 9 條;`--ignore=harness/test_vendor.py` 就是 456 + 1 | **命中** |
| P2 | `pytest harness` = 354 + 1 skipped | 354 passed + 1 skipped(ignore test_vendor);含 vendor 是 363 + 1 | **命中** |
| P3 | `harness_lint` exit 0,三份文件 32 張一致 | exit 0;`ticket-count-in-docs` 0 命中。⚠️ 根 `CLAUDE.md` 被 git mv 走的那段時間,這條規則**靜靜跳過**(檔不在就不查),重建後才又開始查 —— lint 對「文件不見了」沒有牙,記在這裡,沒開票 | **命中**,附一個上限 |
| P4 | `grep -rn tools/harness harness/` 只剩 `run_act2.sh` 6 行 | `run_act2.sh` 6 行 + **4 行歷史敘述**(ADR 0010 ×3、`harness/CLAUDE.md` ×1,都是在講「以前是 tools/harness」) | **命中**(敘述不算引用) |
| P5 | `parents[1-9]` / `../../` 在 harness/ 的 .py .sh 零命中 | **0** | **命中**。但 `acceptance_gwt.py` 還有 `examples/shop/app` 的硬字串(`TEST_REL`、`git archive`),預測的 pattern 沒抓它——它是上游 greenfield 幕三的 gradle 路,hub 本來就不能用(hub-bootstrap 五幕表);沒動 |
| P6 | `vendor.sh` → `diff -r` 只差 `ORIGIN.md`;副本 pytest = P2 | `test_vendor.py` 釘住:`diff -rq` 只差 `ORIGIN.md`;副本印 **354 passed, 2 skipped**(多的 1 skip 是副本裡的 `test_vendor.py` 看到 `VENDOR_INNER` 自己 skip)| **命中**,數字比預測多 1 skip,原因寫在上面 |
| P7 | 再跑一次 → 非 0、「已存在」、檔沒動 | `test_vendor.py` 釘住:exit 1、訊息含「已存在」、`ORIGIN.md` bytes 不變 | **命中** |
| P8 | kc-hub 重搬後 git diff:腳本本體 0 diff;差 ORIGIN / vendor.sh / test_vendor / CLAUDE.md / README | **腳本本體 0 diff**;差的:7 個測試檔 7+/31−(手工刪函式留的空行、段落註解,語意相同)、6 份 md、新 ADR 0010 / vendor.sh / test_vendor.py、**`LICENSE` 少了**(上游 LICENSE 在根,`harness/` 沒有 → 副本沒授權檔;這個 commit 補 `harness/LICENSE`) | **命中**,漏預測測試檔與 LICENSE |

## 沒預測到、要記的

- **文件不見時 lint 不叫**(P3)。`ticket-count-in-docs` 對 `COUNT_DOCS` 裡不存在的檔是 skip 不是 fail。要不要改成 fail 是另一張票的事,先記著。
- 第一個 hub(kc-hub)是「手工搬 → script 重搬取代」,**不算 vendor.sh 零手工的樣本**;vpin-hub 才是(ADR 0010 Consequences 有寫)。
- `harness/LICENSE`:hub 拿走的副本要帶授權,上游根目錄那份留著給 GitHub 看。
