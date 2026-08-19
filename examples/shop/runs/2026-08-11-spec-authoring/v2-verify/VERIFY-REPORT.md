# v2 單臂驗證報告(評分依 pre-registration.md,清單未改動)

日期:2026-08-12。評審:主 session 逐檔讀 out-B2/ 五份原文 + [Qn] 抽查,不採信自報。

## 結論一句

**v2 成立**:五項新槽全數生效(一項部分打折)、舊優點零回歸損失、訪談深度反升
(17 題 vs v1 的 12 題)。殘洞兩個,列為 v3 候選,本輪不動。

## 新槽五項對賬

| # | 檢查 | 結果 |
|---|---|---|
| 1 | DbC 標籤逐條 + 配測試註記 | 🟡 **部分過**:R1–R9 全標、分類合理(R5 postcondition、R6 precondition、餘 invariant),每條有指名測試或不配理由。打折處:**失敗路徑的狀態保證沒有被系統性要求**——九條規則只有 R5 得到 postcondition 標籤,原子性只在 S-03 的 Then 局部覆蓋(查無顧客路徑「未留下任何訂單」)。註:v2 的 domain 無 DRAFT/addItem 生命週期(Order 一次建構、唯一狀態),輪 1 O2 那個洞無法以原形再現;打折是類別層級的:postcondition 這一類仍靠 PM 自己想到 |
| 2 | 五尺度盤點 | ✅ 完整表格、每格結果具體、中尺度「明寫空缺:本輪單 agent」——沒有敷衍 |
| 3 | 不在範圍來源標記 | ✅ 13 項(v1 為 9),訪談否決 7 類 + 規格沉默 6 類 |
| 4 | [Qn] 回鏈 | ✅ 抽查 R5→Q8、R6→Q2/Q3、R9→Q9 全對得上;規則與詞條全數有回鏈;PROMPT 還自發加了「疑義回查 [Qn]」讀取順序 |
| 5 | 金額單位 | ✅ 全線 long minor units,SPEC 數字無歧義(250000 等)——v1 的洞(1500 不知元或分)修掉 |

## 回歸(舊優點)

全過:五檔齊、GWT 真格式(S-01~S-10,具體資料、可斷言 Then)、端點恰兩個、
PROMPT 凍結清單 + 完成定義(6 條,比 v1 嚴:指名測試存在性、命名零違規)+
ASSUMPTIONS 規則(自發加了「規格沉默 ≠ 授權展開」)、腳本 6/6 命中、
術語打槍 fallback 再次觸發(Q12 state machine →「聽不懂,講人話」→ Q13 改口收斂)。

## 預測對賬

| 預測 | 結果 |
|---|---|
| 五項新槽全數出現 | 贏(5/5,其中一項部分打折) |
| 最可能打折:postcondition 貼漏 | **贏**——失敗原子性沒成規則,正中 |
| 盤點可能敷衍一行 | 輸(盤點紮實)——輸得好 |
| 訪談深度不降(≥10 題) | 贏(17 題,反升) |
| DbC 逼出 1–2 題 postcondition 類新 off-script | 半輸——新增 off-script 是角色(Q1)、狀態流轉(Q13)、權限(Q16),沒有失敗留痕類問題;標籤讓分類現形,但沒逼出新問題 |

## 超出預測的兩個行為

1. **好:自發搬階。** A3 要求實作 agent 新增自訂 ArchUnit 規則(domain/usecase 禁
   float/double)、A1 建議自訂規則掃 CustomerRepository 方法名——skill 只要求
   「標注哪些由機械檢查強制」,agent 主動發明了新機械檢查。另自發加
   「邊界例外:無;不得先斬後奏」一節(呼應 INTERFACE-REQUESTS 精神)。
2. **壞:出處誤標(provenance mislabel)。** ARCHITECTURE「常備模板(starter 既定,
   不得偏離)」一節寫了「Repository 介面定義在 domain/」——但工程前提**沒有**給過
   這條;這是 agent 的自決,被標成「既定」。與 H1b 捏造 ASSUMPTIONS 同族
   (沉默處的決定偽裝成給定事實),量級小但型態值得記。

## v3 候選(記下不動)

1. 微尺度盤點檢查句加一格:「postcondition 至少含:每條失敗路徑的狀態保證
   (原子性/不留殘骸)」。
2. ARCHITECTURE 槽位要求出處標記:每條規則標「模板既定 / 本案自決」,
   自決者須有 [Qn] 或 ASSUMPTIONS 依據——防「既定」夾帶。

## 限制

n=1、self-play(榮譽制 + log 審計)、同 model;汙染檢查:參考答案特徵 token
(`unitPriceCents`、`C-001`、`OrderListItem`)未出現(v2 用 minor units/`C001`/
自創 `OrderSummary`→本輪無此詞,列表直接用欄位),無偷看跡象。
