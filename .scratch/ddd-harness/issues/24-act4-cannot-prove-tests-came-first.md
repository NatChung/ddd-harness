# 24 — 幕四的雜湊只查「受保護檔有沒有被改」,查不了「測試是不是在實作之前就在」

**What to build:** `run_act4.sh` 注入完骨架就 `git init` 工作目錄、commit 一版基線,跑完後用
git 首次 commit 時間查:生成的三支測試檔在基線裡、`src/main` 每個檔都在基線之後。
落 `order-check.txt`,三態。

**Blocked by:** None

**Status:** done —— 2026-08-25 `act4_order_check.py` + `test_act4_order.py`(14 條,pytest 236 → 250)+ `run_act4.sh` heredoc 之外的 4b/4c/6b;預測命中 5 / 落空 0(`24-PREDICTION.md` / `24-RESULT.md`)。跟票的形狀兩處刻意不同:歷史放 `harness/act4.git` 不放 `.git`(run 目錄帶 `.git` 會被主 repo 記成 gitlink,實測),所以「agent 自己 commit 照收」不成立;基線 commit 在 `prompt.txt` 寫完之後。真 claude 沒跑過。

## 哪裡壞了

`run_act4.sh` 在注入後算雜湊、跑完再算一次,落 `tamper-check.txt` —— 它證明「受保護檔沒被動」。
它證不了「測試先於實作存在」;那條今天靠幕三 → 幕四的**構造順序**保證,沒有機械檢查
(`PIPELINE.md` 幕四「⚠️ 結構隔離不是防竄改」那段)。

對照(驗過,survey §3 第 13 條):ai-harness-template `check-test-first.sh` L146–208 用
`git log --diff-filter=A` 的首次 commit 時間比測試檔與 source 檔,比 fspec 用 mtime 穩。

## ⚠️ 直接抄會抄到一支永遠不會響的檢查(advisor 2026-08-25)

幕四工作目錄是 **bare dir,不是 git repo**;跑完的產物被一次 commit 進主 repo 的 run 目錄。
「測試首次 commit 早於 source 首次 commit」在那裡**退化成同一個 commit**,永遠相等。
所以形狀要改:

1. `run_act4.sh` 注入骨架 + 三支生成測試之後,在工作目錄 `git init` + `git add -A` +
   `git commit -m "harness-injected baseline"`,**再**呼叫 claude。`ACT4_DRY_RUN=1` 也要做這步
   (不花錢,測得到)。
2. 跑完:`git add -A && git commit -m "agent output"`(或多次也行,agent 自己 commit 的話照收)。
3. 檢查:對 `src/main/**` 每個檔取首次 commit;全部晚於基線 → 通過;有任何一個在基線裡
   → **1**(骨架帶了實作?那是骨架的問題,印出來);三支測試檔任一不在基線 → **1**;
   工作目錄不是 git repo(舊 run)→ **3 不適用**,不折成通過。
4. **上限印在報表**:agent 在工作目錄裡 `git commit --amend` 或重寫歷史就過 —— 這條跟
   雜湊一樣是「查得出,擋不住」;基線 commit 的 hash 寫進 `run-meta.json`,事後能比。

## 慣例(ADR 0007)

「工作目錄必須是 git repo 且有基線 commit」由本檢查守(不是 git repo → 3)。

## 完成的定義

- `test_act4_order.py`(新檔):用 tmp dir 模擬三態;不碰 gradle、不呼叫 claude。
- `24-PREDICTION.md`:對 `runs/2026-08-19-act4/` 的工作目錄(沒 git)跑 → 預期 **3**;
  `ACT4_DRY_RUN=1` 重組一次工作目錄 → 預期通過(只有基線,`src/main` 空)。→ `24-RESULT.md`。
- `run_act4.sh` 檔頭〈已知上限〉加一條。**不動 heredoc 裡的 prompt**(那是受測品,票 13 才動)。
