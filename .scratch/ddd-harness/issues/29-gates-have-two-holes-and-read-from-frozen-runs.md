# 29 — 幕間閘門有三個洞:`gen_*.py` 直接跑繞得過、幕四閘門在本 repo 走不通、證據要寫進不能動的 run 目錄

**What to build:** (a) 幕三閘門搬進生成器本體,同時不動 `test_harness.py`;(b) `acceptance_gwt` 第一段
(空骨架全紅)能對任一骨架目錄單獨跑、單獨記帳,不依賴 `4567d31`;(c) 定「帳本可不可以寫進歷史 run」。

**Blocked by:** None(但 (c) 是拍板題,先 grill 再動)

**Status:** needs-triage —— 2026-08-25 票 21 落地時量到 (a)(b),survey §10 補 (c);尚未開工。

## (a) `gen_*.py` 繞過閘門(驗過,21-RESULT)

閘門放在 `run_act3.sh`,因為 `test_harness.py:515-516` 直接呼叫兩支生成器的 `main()` 釘離開碼。
直接跑 `python3 gen_acceptance.py …` 沒有閘門。**候選**:`main()` 讀 `ACT_GATE=off` 環境變數時跳過閘門、
`test_harness.py` 的 conftest 設它;或閘門查 `--run-dir` 有給才啟動。兩個都是逃生口,**要留痕**
(印一行進 stderr + 帳本記 `gate_skipped`)。不要第三種:改 `test_harness.py`。

## (b) 幕四閘門走不通(驗過,21-RESULT P12)

`acceptance_gwt.py` 的 `stage()` 要 `git archive 4567d31`,那個 commit 在 `kc-log` 沒搬來;而且綁非
`shop-frozen-v1` 合約的 spec 第 2、3 段必不適用 → 整支 3 → 閘門拒絕。閘門**沒放水**,但今天沒有任何真實
骨架能讓幕四閘門通過。要的是:`acceptance_gwt.py --stage 1 <skeleton_dir>` 只跑第一段、只對第一段記帳,
閘門要求的就是這一筆。第 2、3 段的不適用照印,不折進第一段。

## (c) 帳本寫進歷史 run(拍板題)

`check.py` 把 `check-ledger.jsonl` 寫進 `<run_dir>/`。`CLAUDE.md` 硬規則:`examples/**/runs/` 不改。
兩個都對,撞在一起。三個選項,**要 Nat 拍板**:
1. 帳本放 run 目錄外(例:`examples/<case>/harness/ledgers/<run>.jsonl`),閘門去那裡讀 —— 歷史不動,但帳本跟 run 分家。
2. 硬規則加一條豁免:`check-ledger.jsonl` 是 append-only 的 sidecar,**只准新增不准改**,`harness_lint` 加規則守
   「歷史 run 只多了這一個檔」—— 帳本跟 run 在一起,但「不改歷史」的定義變窄。
3. 舊 run 永遠不適用,新 run 起才有帳本 —— 最乾淨,代價是舊素材永遠過不了閘門(票 26 的儀表會一直印 18 張不適用)。

推薦 2(判斷):證據該跟 run 住一起;「只多一個檔」機械查得到。但這改的是 `CLAUDE.md` 硬規則,不能自己決。

## 慣例(ADR 0007)

(a)(b) 由閘門本身守;(c) 選了 2 就由 `harness_lint` 新規則 `frozen-run-only-ledger-added` 守,選 1 / 3 是 prose-only, unenforced。

## 完成的定義

- `29-PREDICTION.md`:對 `examples/shop/app-from-interview/` 跑 `--stage 1` → 預期 12/12 紅、exit 0、帳本一筆;
  之後 `ACT4_DRY_RUN=1 run_act4.sh` **不帶** `ACT_GATE_SKIP` → 預期閘門通過。
- `test_check_ledger.py` 不動;新測試放 `test_gate_holes.py`。
