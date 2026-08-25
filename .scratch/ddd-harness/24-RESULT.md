# 票 24 的實際結果(2026-08-25)

對答案:`24-PREDICTION.md`(commit `08de895`,寫在 `act4_order_check.py` 之前)。

交付:`tools/harness/act4_order_check.py`(新)、`tools/harness/test_act4_order.py`(新,14 條)、
`tools/harness/run_act4.sh`(heredoc 之外:4b 基線 commit、4c `run-meta.json`、dry-run 也查、
6b 跑完 commit + 檢查 + repack、檔頭上限 7)、`PIPELINE.md` 幕四加一段。

## 逐條對預測

| 預測 | 結果 |
|---|---|
| P1 對 `runs/2026-08-19-act4/` 跑 → **3**,而且是「沒有歷史、沒有紀錄」那條 | ✅ 命中。rc=3,第一行【不適用】,理由列「沒有 harness/act4.git,也沒有 run-meta.json 記過基線」 |
| P2 `ACT4_DRY_RUN=1` 重組 → **0** | ✅ 命中。rc=0,「測試檔:3/3 在基線裡」「實作檔:0 個(扣掉受保護的骨架 wiring 2 個與 .gitkeep)」,HEAD = 基線 |
| P3 `run-meta.json` 的 `baseline_commit` = root commit | ✅ 命中。`077ac028…` 兩邊同一個;root commit 只有一個 |
| P4 合成三態(pytest) | ✅ 命中。14/14,總數 236 → **250**;含「有紀錄但歷史不見了 → 1」「住在外層 repo 底下仍 → 3」「改寫歷史 → 1」 |
| P5 上限印在報表 | ✅ 命中。報表尾段印 `commit --amend` / 改寫歷史 / 連 run-meta.json 一起刪三種;有 pytest 釘著它不被拿掉 |

**命中 5 / 落空 0。** 預測裡沒有一條是「不可能失敗」的:P2 的落空條件(`Application.java`
被算成實作)第一版設計就差點踩到 —— 票裡寫「`src/main` 空」,實際骨架的 `src/main` 有 5 個檔,
靠受保護清單 + `.gitkeep` 排除才過。這條寫進了 PREDICTION「動手前先查證過的事」。

## 預測之外做的一件事(驗過)

用 stub `claude`(`HOME` 指到假家目錄,runner 的 `env -i PATH` 第一段是 `$HOME/.local/bin`)
走完 `run_act4.sh` 跑完之後那段:stub 寫一個 `src/main/.../Order.java` + 一支內圈測試。
結果:tamper-check「沒有被動過」、第二個 commit `agent output` 收進 `result.json` /
`run-meta.json` / `tamper-check.txt` / 兩個新檔、order-check **0**(「實作檔:1 個,1/1 首次
出現在基線之後」)、repack 後 `harness/act4.git` 只剩 13 個檔、歸檔形狀(`order-check.txt`
沒 commit)重跑仍 0。**這不是真 claude 跑**,所以 PIPELINE 那段的「沒驗過」還是寫著。

## 跟票的形狀不同的地方(刻意,不是漂移)

1. **歷史放 `harness/act4.git`,不放 `<workdir>/.git`。** git 2.54 實測:工作目錄底下有
   `.git`,外層 `git add` 把整個 run 目錄記成 gitlink(mode 160000),run 的檔案一個都進不了
   主 repo —— 而 run 目錄正是要 commit 進主 repo 當證據的。用 `--git-dir` / `--work-tree`
   分離,外層 repo 把 `harness/act4.git/**` 當普通檔收(實測,13 個檔)。
   **代價**:票裡「agent 自己 commit 的話照收」那句不成立 —— agent 看不到那是 git dir。
   檢查只分得出「基線裡 / 基線之後」。寫進 runner 檔頭上限 7 與報表上限。
2. **基線 commit 在 `prompt.txt` 寫完之後**,不是票寫的「注入骨架 + 三支測試之後」——
   基線 = agent 開工時看到的那棵樹,`prompt.txt` 少了就是 provenance 說謊。
3. **「在基線裡」用樹的成員,不用首次 commit 時間。** 線性歷史下兩者等價,樹成員少一個
   時間解析的來源。`run-meta.json` 記的 hash 跟 root commit 對不上 → 1,那條是「事後能比」
   真的接上的地方。
4. **受保護清單從基線 commit 讀**,不讀工作樹 —— 歸檔後結果決定性,也少一個 agent 可寫的洞。
5. **有紀錄說做過基線、歷史卻不見了 → 1**,不是 3。3 只留給「從來沒有基線」(舊 run)。
   不然 agent `rm -rf harness/act4.git` 就能把自己變成「不適用」。

## 沒做到 / 沒驗過

- **真 claude 沒跑**(要錢,而且 `run_act4.sh` 的 prompt 是受測品,不在本票範圍)。
  agent 環境多了 `harness/act4.git` 這個目錄,跟 2026-08-19 那跑的環境不完全一樣 —— 下次
  真跑要記在 RESULT 裡。
- ADR 0007 要的「慣例二選一」:「工作目錄必須有基線歷史」這條由本檢查守(不是 → 3),
  **有交機械檢查**;但 `harness_lint.py`(票 22)還不存在,票上的〈慣例〉一節沒有規則名可指。
