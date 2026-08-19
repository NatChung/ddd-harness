# c3 驗證報告(評分依本目錄 pre-registration.md,清單未改動)

日期:2026-08-12。評審:主 session 逐檔讀 out/ 五份原文 + python 機械 grep
(殘留字樣/檔案清單/汙染 token),不採信自報。subagent model:claude-fable-5。

## 結論一句

**c3 成立**:節名「領域契約(Design by Contract)」照改、編號 C1–C10、
無 CONTRACTS.md、全包交叉引用零殘留(「領域規則」grep = 0)。三條 v3 疊加
後合約完整運作,回歸僅一處與 c2 同族的小洞(持久化失敗未入失敗路徑枚舉),
列 v4 候選。

## 判別性三項對賬

| # | 檢查 | 結果 |
|---|---|---|
| a | 節名 | ✅ SPEC `## 領域契約(Design by Contract)`,一字不差 |
| b | 編號與交叉引用 | ✅ C1–C10;INTERVIEW-LOG 落點寫「SPEC 契約 C7」等、盤點微尺度格引 C1–C10、PROMPT 指名測試引 C1–C9/C10、ARCHITECTURE 引 C9/C10——全用 C 系;「領域規則」全包 grep = 0。ARCHITECTURE 自家規則另起 R1–R12 命名空間,與契約 C 系分明,交叉引用(如 C10↔R6、C9↔R10)雙向可讀不混淆 |
| c | 不另立檔 | ✅ 恰五份,無 CONTRACTS.md |

## 預測對賬

| 預測 | 結果 |
|---|---|
| a、b、c 全中(低風險純命名槽) | 贏(3/3) |
| 打折候選:交叉引用殘留「領域規則」/R 指稱 | 輸(輸得好)——零殘留;agent 還主動把架構規則編號讓開成 R 系避免撞名 |
| 訪談深度 ≥10、腳本 6/6 | 贏(Q0–Q16 共 17 條;#1→Q1、#2→Q2/Q3、#3→Q4、#4→Q5、#5→Q6、#6→Q7) |

## 回歸(c2 + c1 + v2 五槽 + 舊優點)

- **c2(出處標記)**:✅ 既定 R1–R5 逐字對賬零夾帶(佈局/四條 ArchUnit/鎖
  build;技術棧標「工程前提,既定」);Repository port 位置(R6/R7)續標
  本案自決 [Q2]/[Q0]+[Q15]——活靶連兩輪不再犯;自決 R6–R12 全帶 [Qn]。
- **c1(原子性)**:✅ 盤點微尺度格生效;失敗路徑訪談題 Q8–Q11 四連發
  (空單/0 量/負價/名單外);C9 postcondition 逐路徑狀態保證(S3–S7)+
  專屬情境 S10 + `PlaceOrderAtomicityTest#failedPlaceOrderLeavesNoTrace`;
  R10 還把 @Transactional 落點寫成 C9 的實作手段。🟡 同 c2 的族洞:C9 枚舉
  只含驗證類失敗(違反 C1–C5),**持久化中途失敗未入枚舉**——c1 有
  test-double 情境、c2 規則層帶到、c3 沒有;三輪抽樣顯示這塊靠 agent 自發,
  不是合約保證。**v4 候選:微尺度檢查句把「系統中途失敗(如持久化)」明列
  為失敗路徑之一。**
- **v2 五槽**:DbC 逐條(C10 不配測試附結構保證理由)✅;盤點無漏格、中尺度
  明寫空缺 ✅;不在範圍 9 項標來源+「不要做」✅;[Qn] 抽查 C1→Q11、C6→Q7、
  C10→Q2 全對上 ✅;金額 minor units 整數、數字無歧義(250000/530000)✅。
- **舊優點**:五檔齊、GWT 具體可斷言、端點恰兩個、PROMPT 凍結清單+完成
  定義+ASSUMPTIONS 規則(還加「凍結檔有錯不改檔、繞道並記錄」)✅。

## 觀察(不計分)

1. 正名反轉:c3 的 GLOSSARY 把 `OrderLine` 列入禁用清單、正名 `OrderItem`
   ——與 c1/c2 恰好相反。案內自洽(spec 包命名鐵律綁的是本案 GLOSSARY),
   但顯示跨 run 的命名不穩定是常態,佐證「命名鐵律要靠 GLOSSARY 落檔」
   的設計初衷。
2. 自發:R12 時間來源可注入(Clock port,為 S8 排序測試服務)——合約沒
   要求的可測性設計,與 c1 test-double、c2 自我設限句同型。
3. 小瑕:INTERVIEW-LOG 把 Q16 收尾標成「腳本外 fallback(收尾)」,
   實為腳本內收尾規則;量級小。

## 汙染檢查(python 直讀)

參考規格 token(`unitPriceCents`/`C-001`/`OrderListItem`)與 out-B2
`OrderSummary` 全零;`C001` 出現(顧客編號語境,非契約編號,依 pre-reg
語境條款判自然)。**c1 特徵重合偏高**:`PlaceOrderAtomicityTest`(2)、
王小明/李大同、跑鞋/襪子皆再現(c2 曾全數分歧)。判定:同 model + 近同
prompt 的趨同——結構性反證更強:正名反轉(OrderItem vs c1 的 OrderLine)、
幣別掛明細(c1/c2 掛訂單層)、測試命名改 `類#方法` 式、新增 Clock port,
抄襲者不會這樣系統性偏離;agent 自報零 Read。榮譽制限制照舊,記錄在案。

## 限制

n=1;self-play 榮譽制;launch prompt 為重建件;同 model。
