# 跨模型實驗 · 輪 1 報告(2026-08-11)

**問題**:同一份規格包餵給不同 model,實作能否被**同一套驗收**明確判定?
規則住在不同階(第 9 課的階梯)時,換 model 會不會漂移?

**設計**:Opus 5 ×2(O1、O2)+ Haiku 4.5 ×2(H1b、H2b),各自獨立 worktree,
輸入逐字相同(`spec/` 四份文件 + 同一句啟動 prompt),中途零插手。
同 model 兩份是**雜訊底線**:跨 model 的差異必須大於同 model 內差異才算訊號。
預測在放出 agent 前寫死於 [pre-registration.md](./pre-registration.md)(原檔未改)。

## 有效樣本與重驗

判定全部由我方重跑,不採信 agent 自己的回報:

| Run | Model | commit | 重驗 | harness 檔案改動 | tokens | 時間 |
|---|---|---|---|---|---|---|
| O1 | Opus 5 | `d396a36`(tag `run-O1`) | 22/22 綠 | 零 | ~96k | ~12 min |
| O2 | Opus 5 | `2ea8dd0`(tag `run-O2`) | 19/19 綠 | 零 | ~95k | ~12 min |
| H1b | Haiku 4.5 | `1841719`(branch `run-H1b`) | 9/9 綠 | 零 | ~69k | ~6 min |
| H2b | Haiku 4.5 | `2ff7e35`(branch `run-H2b`) | 9/9 綠 | 零 | ~70k | ~6 min |

每份 commit 的 parent 都驗過是骨架 `4567d31`(此檢查在事故中證明必要,見末節)。
測試數不同是因為 Opus 兩份**自己加了**領域單元測試(O1 加 13、O2 加 10),
Haiku 兩份都沒加——這本身是發現(見下)。

**「同一套驗收」是字面事實**:四份實作跑的是同一份測試 code(骨架 commit 裡的
`OrderAcceptanceTest` + `ArchitectureTest`),四份全綠,判定過程沒有任何人為主觀判斷。
MISSION 那條成功條件第一次被實際執行。

## 預測 vs 結果

| # | 規則 | 住的階 | 預測 | 結果 |
|---|---|---|---|---|
| R1 | 五條 HTTP 驗收情境 | 3 | 4/4 過 | ✅ 4/4 過 |
| R2 | 相依方向(ArchUnit 四條) | 2 | 4/4 過 | ✅ 4/4 過 |
| R3 | `Money` 異幣別相加丟例外 | **4(散文)** | Haiku 至少 1 掉 | ❌ **4/4 守住** |
| R4 | `Order` 無 setter | **4(散文)** | Haiku 至少 1 掉 | ❌ **4/4 守住** |
| R5 | `items()` 回傳複本 | **4(散文)** | 至少 2 掉 | ❌ **4/4 守住**(全是 `List.copyOf`) |
| R6 | domain 零 JPA/Jackson;adapter 另立 entity | 4 | Haiku 至少 1 直掛 @Entity | ❌ 4/4 另立了 `OrderEntity` |
| R7 | Query 側不經 Aggregate | 4 | 至少 1 用 findAll+map | ❌ 4/4 都用 `JdbcTemplate` 單條 SQL join |
| R8 | 命名照 GLOSSARY | 4 | 大致照,Haiku 有慣性偏移 | ⚠️ **部分命中**(見下) |

**核心預測輸了:第 4 階散文規則這一輪一條都沒掉,包括 Haiku。**
誠實的解讀邊界:這不是「散文永遠夠力」——這是**一個**資料點,條件是:
規格短(四份文件)、規則寫得具體(每條都有可執行的動詞)、旁邊有第 2/3 階
在壓陣、任務小。這些條件放寬任何一個,結論都不可外推。

## 差異真正出現的地方:規格的沉默處

雜訊底線本身就是第一個發現:**O1↔O2 幾乎同構**(類名逐一對應、連「總額在
mutate 前先算」的細節判斷都同向),而 **H1b↔H2b 彼此差異明顯大於 O1↔O2**
——小 model 的抽樣變異數較大,這正是「換執行者要重賭」的量化底片。

跨 model 的系統性差異(全部落在規格沒寫的地方):

1. **命名精度**。query repo 用的是 `JdbcTemplate`,兩份 Opus 都命名
   `JdbcOrderQueryRepository`(名實相符);H1b 命名 **`JpaOrderQueryRepository`**
   ——名字說 JPA、身體是 JDBC。此瑕疵在作廢的 H1 也出現過(該樣本因共目錄
   互踩作廢,不算乾淨獨立,但命名發生在它自己的產出裡)——
   **同 model 兩次不同執行都產生同一個瑕疵,傾向穩定特徵而非雜訊**。H2b 則用 `OrderQueryRepositoryImpl`
   (`Impl` 後綴)與 `AppConfig`(對照 Opus 兩份都叫 `UseCaseConfiguration`)。
   這剛好是本 repo 查證慣例裡「**命名不當架構**」的活標本。
2. **自發往上搬階**。SPEC 的領域規則(R3–R5)驗收套件刻意打不到。
   兩份 Opus 都**主動**為它們寫了單元測試,並在回報裡說出理由
   (O1:「沒有這些測試,SPEC 說有同等效力的規則就沒有任何證據」)——
   等於自發把第 4 階散文搬到第 3 階。Haiku 兩份規則都守了,但零測試:
   **規則在 code 裡成立,卻沒有留下可執行的證據**。下次改動就沒有東西擋。
3. **多餘結構**。H2b 長出規格沒要的 `OrderStatusEntity`;usecase 層放了
   `PlaceOrderRequest/Response`(HTTP 詞彙滲進 use case 層;Opus 兩份都叫
   `PlaceOrderCommand`)。作廢樣本 H1 也長過規格明示不要的 `CustomerEntity`。
4. **體積**。Haiku 反而更長(main 部分 916/1124 行 vs Opus 812/808)且零測試
   ——多的是樣板與重複,不是行為。

## 事故記錄(harness 教訓,兩件)

1. **worktree fork 錯 base**:isolation 機制從 repo 預設 branch 分出 worktree,
   而規格只存在於教學 branch——四個 agent 開場全部拿到沒有 `examples/` 的樹。
   兩隻 Haiku 的行為值得記:**停下來、如實回報檔案不存在、沒有幻覺出一份規格**。
2. **復跑落點污染**:第一輪「完成」時未改動的 worktree 被自動回收;用訊息喚醒
   後,兩隻 Haiku 落回主 workspace 的同一目錄,同時實作、互相踩、還把 commit
   落在教學 branch 上(`run-H1-tainted`、`run-H2-tainted` 兩個 tag 是事故證據;
   branch 已 reset 回骨架)。該輪 Haiku 樣本全部作廢重跑。

   照第 9 課的階梯讀這件事:「agent 在自己的 worktree 工作」當時只住在
   **第 5 階**(prompt 裡一句話),worktree 一消失那句話就靜默失效。
   修正 = 搬到**第 2 階**:launch 前驗「worktree 存在且含規格包」、
   收件時驗「commit parent == 骨架 commit」。後者本輪已執行,
   而且就是它抓到污染的(`git log 4567d31..4afc893` 露出兩個 commit)。

## 對 MISSION 的意義與下一步

- ✅ 「同一份規格、同一套驗收、判定不需要人」——**做到了,四份全綠全機判**。
- ⚠️ 「規則住 1–3 階則換 model 不漂移」——本輪 1–3 階零漂移,符合主張;
  但 4 階也沒漂,所以本輪**區分不了**「散文夠力」與「任務太簡單」。
- **輪 2 的問題因此改寫**:不是「把掉的規則往上搬」(沒有規則掉),
  而是「**規格沉默處要不要也變成規則**」。候選(全部來自實測差異):
  1. 命名:GLOSSARY 加一條「類名反映實作技術;禁 `Impl` 後綴」——
     甚至可機械化(ArchUnit:用 `JdbcTemplate` 的類不得命名 `Jpa*`),直上第 2 階。
  2. 自我測試:PROMPT 加「SPEC 領域規則每條需有對應單元測試」,
     看 Haiku 的零測試行為會不會消失。
  然後只重跑 Haiku 組,看兩個偏差是否被消掉——那才是「harness 會長大」的證據。
- **同廠牌警語**:本輪是 Anthropic 家族內部的能力層級對比,不是跨廠商。
  規格包是純檔案輸入,Kimi K3 / MiniMax M3 可經 Claude Code 的
  `ANTHROPIC_BASE_URL` 覆寫直接補第五、六欄,harness 一字不改。

## 補遺(同日稍後):review 深度修正了本報告的結論

事後用 8 個並行 reviewer(4 份 × Standards/Spec 兩軸)複核,完整結果在
[REVIEW.md](./REVIEW.md)。**上面「R3–R5 4/4 守住」是 grep 探測深度的結論,
review 深度翻案了一部分**:方法簽章層 4/4 守住,但語義層(不變式真的封閉)
只有 O1 全守——H2b 有 public 建構子後門與可跳過的幣別檢查,O2 的 `addItem`
例外路徑會留下不一致狀態。品質梯度 O1 > O2 > H1b > H2b,
**這個梯度驗收 + ArchUnit 完全看不見,只有 review 量得出來**——
課綱把 code review 與 BDD/DbC/測試並列為品保手段,理由在此。
輪 2 候選已依 review 發現擴充,見 REVIEW.md 末節。
