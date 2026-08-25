# 票 24 的預測(寫在寫程式之前,2026-08-25)

形狀由票 24 那節「⚠️ 直接抄會抄到一支永遠不會響的檢查」定死:工作目錄自己要有 git 歷史、
注入完就 commit 一版基線,跑完再 commit,檢查看的是「檔案第一次出現在哪個 commit」。
這份只釘兩件事:**拿真實 run 跑會拿到哪一碼**、**dry run 重組一次會拿到哪一碼**,
而且每一條都寫得出什麼結果會讓它落空。

「檢查跑得起來」「pytest 全綠」不可能失敗,**不用**。

## 它做什麼

`tools/harness/act4_order_check.py <workdir>`,`run_act4.sh` 在跑完(與 dry run 組完)
之後呼叫它,stdout 落 `<workdir>/order-check.txt`。三態:

| 離開碼 | 意思 |
|---|---|
| 0 | 三支生成測試檔全在基線裡,而且 `src/main/**` 每個**實作**檔都在基線之後才首次出現 |
| 1 | 任一測試檔不在基線 / 任一實作檔在基線裡(骨架帶了實作)/ 基線紀錄與歷史對不上 |
| 2 | 用法錯誤(吃錯目錄) |
| 3 | **不適用** —— 工作目錄沒有 git 歷史(舊 run)。**不折成通過**,印在最上面 |

## 動手前先查證過的事(不是預測,是事實)

- `runs/2026-08-19-act4/` **沒有** `run-meta.json`,也沒有任何 `.git` / git 歷史;
  它自己就住在主 repo 裡,所以在那個目錄跑 `git rev-parse --show-toplevel` 會回**主 repo**
  —— 「是不是 git repo」的判準不能用「git 認不認得」,得用「工作目錄自己那份歷史在不在」。
- 骨架 `examples/shop/app-from-interview/src/main/` **不是空的**:`Application.java`、
  `application.properties`、三個 `.gitkeep`。票裡寫的「`src/main` 空」不精確 ——
  dry run 能通過,靠的是**把受保護清單(`harness/protected-baseline.txt`)裡的檔與 `.gitkeep`
  排除在「實作檔」之外**,不是靠 `src/main` 真的空。
- 主 repo 用 git 2.54 實測:工作目錄底下放一個 `.git`,外層 `git add` 會把整個 run 目錄
  記成 **gitlink(mode 160000)**,run 的檔案一個都進不了主 repo。所以工作目錄的歷史
  放 `harness/act4.git`(`--git-dir` / `--work-tree` 分離),外層 repo 把它當普通檔案收。
  實測過:`info/exclude` 擋住它 track 自己;`--template=` 不產 sample hooks。

## 決定(不是預測)

- **基線 commit 在 `prompt.txt` 寫完之後、呼叫 claude 之前** —— 基線 = agent 看到的那棵樹,
  一個檔都不少。`run-meta.json`(含基線 hash)在基線 commit 之後寫。
- **agent 自己的 commit 不會進這份歷史**(它看不到 `harness/act4.git` 是 git dir,
  除非它去找)。這偏離票裡「agent 自己 commit 的話照收」那句 —— 換來的是不會踩 gitlink。
- 「實作檔」= HEAD 裡 `src/main/**` 扣掉受保護清單與 `.gitkeep`;受保護清單**從基線 commit 讀**
  (`git show <基線>:harness/protected-baseline.txt`),不讀工作樹。
- 「測試檔」= HEAD 裡 `src/test/**` 全部,每一個都必須在基線裡(受保護清單裡的三支自然含在內);
  被刪掉的測試檔本檢查不管 —— 那是 `tamper-check.txt` 的事。

## 預測(逐條可落空)

### P1 對 `runs/2026-08-19-act4/` 跑 → 離開碼 **3**,而且是「沒有 git 歷史」那條 3

它沒有 `harness/act4.git`、也沒有 `run-meta.json`,所以走「從來沒有基線」那條路。
報表第一行要印【不適用】,不是任何形式的通過或失敗。

→ 落空條件:回 0(把「沒有歷史」折成通過 —— 票裡明講不准)、回 1(把舊 run 當竄改)、
  回 2(把它當吃錯目錄 —— 它是合法的工作目錄,只是舊)。

### P2 `ACT4_DRY_RUN=1` 重組一次 → 離開碼 **0**

工作目錄放 `/private/tmp/claude-501/…/scratchpad/` 底下,不進 repo。
基線裡:三支測試檔 + 受保護清單;`src/main/**` 扣掉受保護與 `.gitkeep` 之後 **0 個實作檔**;
HEAD = 基線(dry run 沒有第二個 commit)。報表要印「測試檔 3/3 在基線、實作檔 0 個」。

→ 落空條件:回 1 —— 最可能的原因是 `Application.java` / `application.properties` 被算成實作
  (排除清單沒接上),或 `harness/act4.git` 自己被 track 進去(`info/exclude` 沒生效);
  回 3 —— `git init` 根本沒跑到(dry run 提早 exit)。

### P3 dry run 的 `run-meta.json` 的 `baseline_commit` = `harness/act4.git` 的 root commit

→ 落空條件:兩者不同(寫 meta 的時機在 commit 之前),或 root commit 多於一個。

### P4 合成三態(pytest,tmp dir)

- 基線含測試、之後才加 `src/main/X.java` → 0
- 基線就含 `src/main/X.java`(非受保護)→ 1,而且報表點名那個檔
- 測試檔在基線之後才加 → 1
- 沒有 `harness/act4.git` 且沒有 `run-meta.json` → 3;沒有 git dir 但 `run-meta.json` 記著基線 → **1**
  (紀錄說有過基線、歷史卻不見了 —— 那是異常,不是不適用)
- `run-meta.json` 記的基線 hash 與 root commit 對不上(歷史被改寫過)→ 1

→ 落空條件:任何一格對不上;或 pytest 總數不是 236 + 新增條數。

### P5 上限印在報表裡,而且真的擋不住

`git commit --amend` / 改寫歷史 / `rm -rf harness/act4.git` 再把 `run-meta.json` 也刪掉
→ 三種都能讓檢查回 3 或 0。這條**不是要修**,是要印出來(票 24 第 4 點)。
→ 落空條件:報表沒印;或有人把它當 bug 修掉。
