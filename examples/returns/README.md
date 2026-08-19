# examples/returns —— 訪談 prompt 的跨模型測試案例

跟 `examples/shop/` 的分工:

| | 測什麼 | 產出 |
|---|---|---|
| **`examples/shop/`** | **實作 agent**(第四幕)—— 同一份 spec 餵不同 model,寫出來的 **code** 會不會漂 | Java,靠 `./gradlew test` 機械判定 |
| **`examples/returns/`**(本目錄) | **訪談 agent**(第一、二幕)—— 同一份逐字稿餵不同 model,產出的 **spec** 會不會漂 | markdown,靠指標對賬 |

兩者互補:shop 那邊已經有骨架、驗收測試與 ArchUnit(第三幕做完了);
本目錄**刻意停在 spec**,不做骨架 —— 因為受測的東西是「訪談與落檔」這一段本身。

⚠️ **本案例不進第四幕。** 退貨 spec 目前有未裁決的內部矛盾與阻斷級的規格沉默
(見 `runs/*/baseline-opus/v1-full.md` 的 §5、§7),現在拿去餵實作 agent,
量到的會是「規格有洞」而不是「模型差異」。要測實作漂移請用 `examples/shop/`。

## 檔案

| 檔 | 是什麼 |
|---|---|
| `interview-prompt.md` | 受測品,**只有這一份**。版本住在 git 不在檔名;產出範圍與 skill v4 的五份相當。**目前 blob 尚未測** |
| `transcript-full.md` | 固定輸入 A —— 受訪者全部答滿、無 hedging |
| `transcript-partial.md` | 固定輸入 B —— 受訪者會漏答、會說「先這樣吧」 |
| `runs/<日期>-<slug>/` | 每次 run 的產出與報告 |

**兩份逐字稿一旦有 run 用過就不得修改** —— 改了後續 run 就對不上賬。要改請開新檔
(`transcript-full-2.md`),不要就地編輯。

**prompt 相反:就地改,靠 git 記版本。** 但每份產出都要在 `runs/*/PROVENANCE.md`
記下它由哪個 blob 產生 —— 沒有那一行,產出無法解讀(不知道當時的必填欄有哪些)。
**同一張對賬表只能收同一個 blob 的產出。**

## 這個案例為什麼是「退貨」

需要一個素材同時包含這幾樣,才測得出訪談 prompt 的各個欄位有沒有作用:

- **同名不同義**(客服/倉庫/財務三方各講一件事)→ 測 Bounded Context 與詞彙表
- **兩條真的會打架的規則**(收貨才退錢 vs 查無件直接退)→ 測會不會自行調和
- **一條要推導才看得到的矛盾**(每次進位 × 可分 3 次退 → 退款可能超過實付)
- **一個隱藏的冪等缺口**(重試 3 次沒有冪等鍵 = 重複退款 3 次)
- **四條跨聚合根的規則** → 測 invariant 的「守在哪個聚合根內」那一欄
- **Value Object 與 Domain Event 的素材**

完整清單是**對賬用的答案卷,刻意不放在 repo 裡** —— 受測 agent 在 worktree 裡跑,
repo 裡的東西它讀得到。答案卷在 `~/.claude/handoffs/kc-log/` 的 pre-registration 附錄,
跑完對完賬才隨 `REPORT.md` commit 進來。

## 已有的基線

`runs/2026-08-17-interview-cross-model/baseline-opus/` —— Opus 5 跑 full 逐字稿的兩份產出
(v0 與 v1 各一)。這兩份是後續所有模型的對照組。

**目前只有 Opus、只有 full 逐字稿、每格只跑一次。**
2×2(prompt × 逐字稿)尚未補齊,重複性也還沒測。
