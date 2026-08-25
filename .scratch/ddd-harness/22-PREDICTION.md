# 22 — 預測:`harness_lint.py` 第一次對真 repo 跑會看到什麼

**寫在跑之前**(2026-08-25,`harness_lint.py` 一行都還沒寫;下面的數字全部從已經看過的
語料手算,不是跑出來的)。對答案寫 `22-RESULT.md`。

## 語料(驗過,跑之前已看)

- 票 27 張(`01`–`27`),全部 `NN-kebab-slug.md`,沒有重號。
- **git 首次 commit 日期**(`git log --diff-filter=A --format=%cs`,取最早一筆):
  - 01–18 全部 `2026-08-19`(`e25f0f6`,整個 harness 從 `kc-log` 搬過來那一刀);
  - 19、20 `2026-08-21`;21–27 `2026-08-25`(`87756db`)。
  - `.scratch/ddd-harness/*-PREDICTION.md` 九份全 `2026-08-19`,`16-RESULT.md` `2026-08-24`,
    `10-RESULT.md` `2026-08-19`。
  - 18 個 run 目錄:15 個 `2026-08-19`,timesheet 三個 `2026-08-21`。
- `ADOPTION_DATE = 2026-08-25`,**嚴格之後**才算新(ADR 0007 §2 寫「之後」,Agentheim
  `spike-stop-loss.mjs` 寫 `created <= ADOPTION_DATE → grandfathered`)。
  **所以 21–27 也是祖父票** —— 它們跟祖父日同一天進 repo。
- 三份文件的票數:`CLAUDE.md:13` 「27 張,18 張還活著」、`README.md:151` 「27 張票,18 張還活著」、
  `PIPELINE.md:353` 「共 27 張,9 張已完成」。`CLAUDE.md:23` 「目前到 27,下一張是 28」。

## 逐條預測

| 規則 | 祖父 | 預測:待處理(計入離開碼) | 預測:祖父豁免 | 依據 |
|---|---|---|---|---|
| `ticket-filename` | 否 | **0** | — | 27 個檔名肉眼全合 |
| `status-vocabulary` | 是 | **0** | **3**(06、08 `A 半 done`;09 `resolved`) | 票 22 完成定義自己點名的三張;其餘 24 張第一個詞都在前六個裡(含粗體包起來的 `**done**`、`**blocked**`) |
| `status-single-cell` | 是 | **0** | **0** | `grep -c '^\*\*Status:\*\*'` 27 張全是 1 |
| `prediction-before-result` | 否 | **0** | — | 只有 10、16 兩對;10 同 commit(相等不算晚),16 的 PREDICTION 08-19 < RESULT 08-24 |
| `prediction-before-run` | 是 | **0** | **0** | 有 PREDICTION 的票(03/05/06/08/10/11/12/16)引用的 run 全是 `e25f0f6` 同 commit 或更晚(16 → `2026-08-21-act2`)。**這條在現在的語料上幾乎沒資訊**:搬 repo 那一刀把所有舊日期壓成同一天 |
| `referenced-run-exists` | 否 | **0** | — | 票裡出現的 15 個不同 `runs/<name>` 逐一對過 18 個目錄,全在 |
| `blocked-by-resolvable` | 是 | **0** | **0** | Blocked by 提到的票號:01、06、10、12、21,全存在;票 27 的「ADR 0008」不是票號 |
| `convention-undecided`(佇列) | 是 | **0**(佇列不計入) | **3**(24、25、26) | 21–27 七張都含立規詞;21、22、23、27 有 `harness_lint` 或 `prose-only, unenforced`,**24、25、26 沒有** → 進佇列,但同日 commit 所以是祖父 |
| `ticket-count-in-docs` | 否 | **0** | — | 三處都已在 `87756db` 修成 27,實際 27。票 22 完成定義寫的「合併前命中 3 處」**在本票開工前就被 `87756db` 作廢了** |

**離開碼預測:0**(待處理 0 筆;祖父豁免 3 + 佇列 3 不計入)。

## 副預測

1. 本票做完把 22 的 Status 改成 `done` 之後,三份文件的「18 張還活著 / 9 張已完成」會變成假的
   (17 / 10)。`ticket-count-in-docs` **刻意只查總數**(這條祖父=否,查活票數就會逼著每關一張票
   改三份文件,而且「活著」的定義得先拍板)—— 所以 lint 不會叫,但我會在同一個 commit 手動改成
   17 / 10,並在 RESULT 記下這是 lint 抓不到的一類漂。
2. `prediction-before-run` 的「同一 commit 一起進來分不出先後」上限,在這個 repo 不是邊角案例,
   是**主案例**:`e25f0f6` 一刀把 01–18 全部票、九份預測、15 個 run 壓成同一天。

## 落空的話怎麼讀

- 祖父=否的規則有任何一筆待處理 → **那是發現,寫進 RESULT,不改資料、不改規則**(票 22 慣例節)。
- `status-vocabulary` 豁免數 ≠ 3 → 先看是不是我的「第一個詞」解析法漏掉粗體 / 全形括號,
  fixture 分得出是 lint 的 bug 還是語料真的不一樣。
- `convention-undecided` 佇列 ≠ 3 → 關鍵字表(慣例 / 規約 / 一律 / 必須)或「引用了規則名」
  的判法跟我手算的不同,列出差異。
