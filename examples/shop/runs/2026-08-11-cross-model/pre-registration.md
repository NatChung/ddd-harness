# 跨模型實驗 —— 事前預測(pre-registration)

寫於 2026-08-11,**在放出任何 agent 之前**。實驗後逐列對答案,寫進 runs/ 的報告。
刻意不放進 repo(agent 會讀到),實驗結束後才隨報告 commit。

## 設計

- 4 個 agent:Opus ×2(O1、O2)、Haiku 4.5 ×2(H1、H2),各自 worktree。
- 同 model 兩份 = 雜訊底線:O1↔O2、H1↔H2 的差異是抽樣雜訊,
  跨 model 的差異要大於它才算訊號。
- 輸入逐字相同:spec/ 四份文件 + 同一句啟動 prompt。中途不插手。

## 規則 × 住的階 × 預測

| # | 規則 | 住第幾階 | 預測 |
|---|---|---|---|
| R1 | POST /orders 回 201+orderId、列表五情境 | 3(驗收套件) | 4/4 過 |
| R2 | domain/usecase 不 import 框架、usecase 不 import adapter | 2(ArchUnit) | 4/4 過 |
| R3 | `Money` 不同幣別相加丟例外 | **4(只在 SPEC 散文)** | Opus 2/2 做到;Haiku 至少 1 掉(或根本不做 Money 運算、金額用裸 long) |
| R4 | `Order` 無 setter | **4(只在 SPEC 散文)** | Opus 2/2 守住;Haiku 至少 1 掉(JPA entity 誘導) |
| R5 | `items()` 回傳複本 | **4(只在 SPEC 散文)** | 4 份裡至少 2 掉,Haiku 2/2 掉(最可能:根本沒寫 items() 或直接回本體) |
| R6 | 領域物件不掛 JPA/Jackson annotation,adapter 另立 OrderEntity | 4(ARCHITECTURE 散文;ArchUnit 只擋 import,擋不住「不另立模型」…實際上 domain 掛 annotation 會被 R2 抓到,但 usecase 繞過 domain 直寫 entity 不會) | Opus 2/2 另立;Haiku 至少 1 直接把 @Entity 掛上領域物件 → 會被 ArchUnit 紅燈逼回來,看它怎麼繞 |
| R7 | Query 側不經 Aggregate(不 findAll+map) | 4(ARCHITECTURE 散文) | Haiku 至少 1 用 findAll 再 map;Opus 可能 1 個也這樣(這條最容易被忽略) |
| R8 | 詞彙服從:類名照 GLOSSARY(PlaceOrderUseCase 等) | 4(GLOSSARY) | 4/4 大致照;偏差最可能出現在 Haiku 的 service/dto 命名慣性(OrderService、OrderDto) |

## 判定方式(事後)

- R1、R2:測試結果,機器判。
- R3–R5:對 4 份 code 跑同一組「探測」:grep setter、讀 Money.plus、讀 items()。
- R6–R8:人工讀 diff,但判準是上表寫死的,不臨場發明。

## 預測的總結論

若 R3–R5 如預測掉在 Haiku 側:驗證第 9 課「4 階規則換 model 重賭」的主張,
輪 2 就把掉的那條往上搬(R4 → ArchUnit no-setter 規則是現成的第 2 階搬法)再跑。
若 4/4 全守住(沒高潮):代表 SPEC 散文對這兩個 model 都夠力,把能力差距拉大
或把規則再降階(從 SPEC 移到只在 PROMPT 提一句)再測。
