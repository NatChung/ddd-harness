# 26 — 五支檢查器各自印「不適用」,沒人跨跑統計:守衛靜靜不再適用,要等人翻報表才發現

**What to build:** `tools/harness/na_ratio.py`:讀各 run 的 `check-ledger.jsonl`(票 21),
按檢查器算 通過 / 未過 / 不適用 / 跳過 的比率;超過門檻就印警告;runner 開頭順帶印一行。

**Blocked by:** 票 21(帳本格式由它定)

**Status:** blocked —— 2026-08-25 Nat 拍板要做(survey §9 #10),等票 21 合併後開工。

## 哪裡壞了

`PIPELINE.md` 幕一那段的實測:題號寫法從 `**Q1.` 改成 `**Q1:`,守衛整份不適用而 exit 0
(2026-08-18 修成 exit 3)。修了之後**每一跑都會誠實印「不適用」** —— 但連續十跑都不適用,
今天沒人會注意。「不適用」被看見的前提是有人在看。

對照(**宣稱**,survey §3 第 17 條,只讀 README):Harmonist 記 `PROTOCOL-SKIP` 的比率,
超過 25%(至少 5 次)就在下一個 session 開頭警告。**抄形狀,門檻自己量。**

## 形狀

- 輸入:`examples/**/runs/*/check-ledger.jsonl`(票 21 起才有;舊 run 沒有 → 那些 run **不適用**,
  印張數,不折進分母)。
- 輸出:一張表,列 = 檢查器,欄 = 跑過幾次 / 0 / 1 / 3 / skip;最後一欄「連續不適用 N 次」。
- 門檻:先不擋。`--warn-threshold 0.25 --min-runs 5` 預設,超過印 ⚠️;離開碼永遠 0 或 2 或 3
  (沒有任何帳本 → 3)。**它是儀表,不是閘門** —— 升成閘門要另開票。
- runner 開頭那一行:`run_act2.sh` / `run_act4.sh` 啟動時呼叫一次,印「上 N 跑 landing_check 不適用 M 次」。

## 慣例(ADR 0007)

「帳本格式」歸票 21;本票只讀。讀不動的行:跳過並計數印出(loss-tolerant),不 crash。

## 完成的定義

- `test_na_ratio.py`(新檔):三份合成帳本 → 表正確、門檻警告、零帳本 → 3。
- `26-PREDICTION.md`:對合併票 21 之後**現有**的 run 跑 → 預期「全部不適用(沒有帳本)」、exit 3。
