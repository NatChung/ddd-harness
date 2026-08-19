# v4 驗證報告(評分依本目錄 pre-registration.md,清單未改動)

日期:2026-08-12。評審:主 session 逐檔讀 out/ 五份原文 + python grep,
不採信自報。subagent model:claude-fable-5。

## 結論一句

**v4 成立**:三輪抽樣裡靠 agent 自發的「持久化中途失敗」覆蓋,合約點名後
一次到位——訪談長出專屬技術題(Q15)、契約枚舉明含(C7)、專屬情境 S9 的
test double 設計成「部分資料已寫入後失敗」且 Then 要求**先斷言失敗確實被
觸發**——預測的打折點(防空洞機制缺席)沒有發生。skill 至此四版四驗全過。

## 判別性三項對賬

| # | 檢查 | 結果 |
|---|---|---|
| a | 盤點格生效 | ✅ 微尺度格明列持久化中途失敗+指名測試+不得空洞,結果具體 |
| b | 入契約枚舉 | ✅ C7 枚舉明含「系統中途失敗(如持久化中途失敗)」,並附失敗路徑清單一行(查無顧客/驗證類/混幣別/持久化中途失敗) |
| c | 不空洞的指名測試 | ✅ S9:test double「在部分資料已寫入後失敗」+ Then「先斷言例外確實被觸發,再實查訂單/明細筆數為 0」;`CreateOrderAtomicityTest#midPersistenceFailureLeavesNoResidue`;PROMPT 硬規則再重申一次不得空洞 |

## 預測對賬

| 預測 | 結果 |
|---|---|
| a、b 中(合約直給) | 贏 |
| 真考驗在 c,最可能打折:Given 沒寫「部分寫入後才失敗」 | 輸(輸得好)——Given 明寫部分寫入後失敗,還加了「先證明失敗發生」的斷言順序 |
| 訪談深度 ≥10、腳本 6/6 | 贏(16 題;#1→Q1、#2→Q2/Q3、#3→Q4、#4→Q5、#5→Q6、#6→Q7) |

## 回歸(c1–c3 + v2 五槽 + 舊優點)

- **c3**:「領域契約(Design by Contract)」節名 ✅、C1–C8 ✅、無 CONTRACTS.md
  ✅、「領域規則」grep=0 ✅。
- **c2**:既定 T1–T6 逐字對賬零夾帶(技術棧標「工程前提,既定」);自決
  A1–A6 全帶 [Qn];Repository port 位置只在 GLOSSARY 所屬層欄出現
  (domain 介面/adapter 實作,掛 [Q13][Q14]),未偽裝既定 ✅。
- **c1**:盤點原子性格 ✅;失敗路徑題 Q9/Q10(業務)+Q15(技術,「存到
  一半失敗怎麼辦」)✅;S2–S6 各 Then 斷言零殘留 ✅。
- **v2 五槽**:DbC 逐條配指名測試 ✅;盤點無漏格、中尺度明寫空缺 ✅;不在
  範圍 10 項標來源(含「CRM 同步機制」這種訪談只確認到一半的誠實沉默項)✅;
  [Qn] 抽查 C1→Q10、C4→Q7、C7→Q15 全對上 ✅;金額 cents 整數無歧義 ✅。
- **舊優點**:五檔齊、GWT 具體、端點恰兩個、PROMPT 凍結+完成定義
  +ASSUMPTIONS(加「spec 矛盾停下回報,不得自行改 spec」)✅。

## 觀察(不計分)

1. **自發搬階第四例**:`EndpointInventoryTest#exactlyTwoEndpoints`(列舉
   Spring handler mappings 斷言端點恰兩個)——「端點不多不少」歷代都靠
   文字約束,本輪 agent 自發把它機械化成指名測試。
2. 交易邊界出現第三種答案:c1=usecase、c2/c3=adapter、v4=「語意在 usecase、
   框架機制由 adapter 組裝提供(維持 T3)」——同一自決點三輪三樣,
   出處標記制度讓這個分歧全程可見、可裁決。
3. 正名再反轉:v4 回到 `OrderLine` 為正名、`OrderItem` 入禁用(與 c3 相反、
   與 c1/c2 相同)——再證命名跨 run 不穩定,GLOSSARY 落檔是對的設計。

## 汙染檢查(python 直讀)

`C-001`/`OrderListItem`/`OrderSummary`/`unitPriceMinor` 全零;`unitPriceCents`
出現(同 c1 的灰色判定:skill 例句「金額一律 cents 整數」可自然導出,無其他
參考特徵伴隨);`C001`/王小明高自然度;c1 特徵測試名 `PlaceOrderAtomicityTest`
零(本輪 use case 自名 CreateOrder,測試名隨之分歧);商品(鞋/襪 vs 跑鞋/
襪子)、第二顧客(李大華,同 c2 不同 c1)混合分佈——判獨立生成。
agent 自報:零 Read、未跑 git。

## 限制

n=1;self-play 榮譽制;launch prompt 為重建件;同 model。
pre-reg 已先認:c 的證據力受「c1 同型設計已入 repo」限制,判讀以
「有沒有做」為主——本輪測試名、use case 名、斷言順序設計皆與 c1 有別,
獨立性佐證比預期強。
