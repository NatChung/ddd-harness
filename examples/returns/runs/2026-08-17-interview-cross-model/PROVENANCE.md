# 產出 ↔ 受測 prompt 的對應

**受測 prompt 只有一份:`examples/returns/interview-prompt.md`。版本住在 git,不在檔名。**

每一份產出必須記下它是由**哪個 blob** 產生的。沒有這一行,產出無法解讀
——你不知道當時的必填欄有哪些。沿用 repo 既有慣例(每輪 pre-registration 釘 blob hash)。

| 產出檔 | prompt blob | 當時的檔名 | 逐字稿 | 模型 |
|---|---|---|---|---|
| `baseline-opus/v0-full.md` | `8bcaf8e44e39` | `interview-prompt-v0.md` | full | Opus 5 |
| `baseline-opus/v1-full.md` | `be2a6df0aebf` | `interview-prompt-v1.md` | full | Opus 5 |
| `v0-partial-opus-1.md` | `8bcaf8e44e39` | `interview-prompt-v0.md` | partial | Opus 5 |
| `v1-partial-opus-1.md` | `be2a6df0aebf` | `interview-prompt-v1.md` | partial | Opus 5 |

**目前 HEAD 的 prompt** = blob **`71c1eb7d6eb6`**
(產出範圍已補齊至與 skill v4 相當:多了 §9 ARCHITECTURE、§10 PROMPT、§11 INTERVIEW-LOG;
2026-08-17 又剝掉了非指示內容,見下)。
接下來的跨模型 run 全部用它,產出檔名為 `partial-<model>-<第幾次>.md`。

## 剝離(2026-08-17):為什麼跑之前要先動受測品

`37649fc5aa02` 的檔末「改動紀錄」**點名了 14 條必填欄裡的 6 條**,每條還附「前幾輪漏掉這個」:

| 改動紀錄條目 | 對到的必填欄 |
|---|---|
| #3 補 Value Object / Domain Event / 系統中途失敗 | 1、2、4 |
| #4 加「守在哪個聚合根內」必填欄 | 3 |
| #1 `模板既定` 加文件白名單 | 6 |
| #6 §11 逐題落點對照 | 10 |

**這不是洩答案** —— §6 產出合約本來就要求這些欄。**是差別放大**:14 欄裡 6 欄被額外強調
且附失敗史,另外 8 欄沒有。而本實驗的產出是**一張欄位的搬階清單**,也就是一份排序
—— 差別放大器污染的正是那份排序。

第二層:**skill v5 不會帶著這張改動紀錄**。留著它,量到的穩定度會**高估** skill 真正
繼承得到的東西。

所以剝離對實驗是加分,不是岔路。四處刪除,**一行指示都沒動**(程式驗過:舊檔套上這 4 處
刪除,逐位元組等於新檔):檔頭 blockquote、§6 開頭的 skill v4 對照表、§11 的「v2 唯一新機制」
註解、檔末改動紀錄 + 版本狀態。改動紀錄搬到 `../../interview-prompt-rationale.md`
(併進 skill v5 時要用,那是每條機制的依據)。

代價:`37649fc5aa02` 跑的 `opus-1`(15.3 分、$4.02)作廢重跑。

> 諷刺的地方:`435c964` 立的規矩是「版本住在 git,不在檔名」。把改動紀錄嵌在受測品裡,
> 違反的是同一條規矩,而且代價比檔名大得多。

> ⚠️ **2026-08-17 更正**:本檔與 `LAUNCH.md` 原本把現行 blob 記成 `3654958ef08a`,
> **那是錯的**。`3654958ef08a` 是 commit `48cb4f2` 時的舊檔名 `interview-prompt-v2.md`;
> 改名收成一份的 commit `435c964` 同時改了檔頭,blob 因此變成 `37649fc5aa02`。
> 兩者實質差異**只有檔頭那段版本說明**(`git diff` 過:正文、六節產出合約、八節完成判準
> 一字未動),所以 14 條必填欄照舊適用。但 blob 記錯就是對賬表對不上,已就地更正。
> 這正好是本檔「紀律」那節在講的事 —— 而它自己犯了。

## 要看某個 blob 的內容

```bash
git cat-file -p 8bcaf8e44e39          # 舊 v0
git cat-file -p be2a6df0aebf          # 舊 v1
git log -p --follow -- examples/returns/interview-prompt.md   # 完整演進
```

舊的 v0 / v1 檔案已從工作區刪除(git 留著)。要重跑舊版做對照:

```bash
git show 8bcaf8e44e39 > /tmp/prompt-v0.md
```

## 紀律

**改了 prompt 就是新 blob,舊產出不會因此失效,但也不能拿來跟新 blob 的產出混在一張表裡比。**
每張對賬表只能收同一個 blob 的產出。
