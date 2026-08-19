# Pre-registration:v3 c1 —— 盤點微尺度加原子性判準(寫於放 agent 之前)

日期:2026-08-12。單臂 n=1、self-play,只驗這一條新槽,不是模型實驗。

## 變因

- **唯一 skill 變更**(對 v2 文本):五尺度盤點微(契約)格由
  「每條領域規則有 DbC 標籤?」改為
  「每條領域規則有 DbC 標籤?postcondition 至少含:每條失敗路徑的狀態保證
  (原子性/不留殘骸)?」(另標題 v2→v3,純版本標記)。
- Skill 全文 hash:記於本檔末(commit 後補)。
- Launch prompt:`../launch-prompt.md`(凍結;**為重建件,非 v2 原件逐位元組**,
  c1–c3 間同條件由該檔保證)。
- 其餘與 v2 驗證同條件:同腳本化 stakeholder、同工程前提、同 self-play
  與禁讀規則(榮譽制 + 自報審計,無硬隔離)。

## 判別性檢查(這一輪的主指標,先寫死)

v2 的正中預測:失敗原子性沒成規則、也沒逼出失敗路徑類 off-script 問題。
c1 過 = 以下三項全中:

- **a. 盤點格生效**:五尺度盤點微尺度格出現原子性判準(字樣或等義),
  且結果具體(不是照抄檢查句)。
- **b. 訪談現形**:INTERVIEW-LOG 至少一題失敗路徑/失敗留痕類問題
  (預期走 off-script fallback「沒想過,先照你的建議」,PM 建議被記錄
  且有 [Qn])。
- **c. 落到契約**:SPEC 領域規則節至少一條 postcondition 標籤契約,
  內容是失敗路徑的狀態保證(例:下單失敗不得留下任何部分訂單),
  並配指名測試或一句不配理由。

**先認的邊界**:若本輪 domain 又長成一次建構、無生命週期(v2 即如此),
失敗面本來就窄——判準是「**列舉出的每條失敗路徑**都有狀態保證」,
不是 postcondition 的數量;讀端點(列表)無寫入,無原子性義務。

## 回歸檢查(逐輪累加;本輪 = v2 全套)

- v2 五槽:DbC 標籤逐條+配測試註記、五尺度盤點(中尺度明寫空缺:本輪單
  agent)、不在範圍逐項標來源、[Qn] 回鏈抽查 3 條、金額單位定死。
- 舊優點:五檔全齊、GWT 真格式且 Then 可斷言、端點恰兩個、PROMPT 凍結
  清單+完成定義+ASSUMPTIONS 規則、訪談腳本命中 6/6。

## 預測(輸贏以此為準)

- a 幾乎必中(表格是合約直給);**真考驗在 b**——v2 這裡半輸
  (標籤讓分類現形,但沒逼出新問題)。預測 c1 的新檢查句能逼出
  至少 1 題失敗路徑 off-script,b 中。
- c 中,但最可能打折處:失敗路徑列舉不全(只顧下單主路徑的驗證失敗,
  漏掉持久化失敗這類 PM 想不到的);打折不算全輸,照邊界條款計。
- 訪談深度不降:≥10 題、腳本 6/6。

## 汙染檢查(審計時跑,rtk proxy 或 python,防 hook 假陰性)

- 參考規格(4567d31)特徵 token:`unitPriceCents`、`C-001`、`OrderListItem`。
- out-B2(已入 repo)特徵 token:`OrderSummary`、`C001`。
- 任一出現 = 逐條人工判斷是否自然重合,寫進報告。

## 限制

n=1;self-play 洩漏同前;同 model(subagent 繼承主 session model =
claude-fable-5,v2 當輪 subagent model 未留記錄,此後每輪記錄);
launch prompt 為重建件(見上)。

## Skill hash

- `.claude/skills/spec-authoring/SKILL.md` blob = `17ee7e72367697f3840fb054c1176c992ad35d84`
  (blob hash 不隨 commit 變,開跑前即可釘死)
