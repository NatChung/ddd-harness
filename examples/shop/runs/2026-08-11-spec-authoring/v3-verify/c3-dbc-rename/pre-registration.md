# Pre-registration:v3 c3 —— 「領域規則」改名「領域契約(DbC)」、編號 R→C(寫於放 agent 之前)

日期:2026-08-12。單臂 n=1、self-play,只驗這一條(疊在 c1+c2 之上)。
Nat 已拍板:不另立 CONTRACTS.md,契約留在 SPEC 內。

## 變因

- **唯一 skill 變更**(對 c2 文本):產出合約第 2 條(SPEC)的
  「領域規則獨立一節」改為「**『領域契約(Design by Contract)』獨立一節**
  (節名用此名,不另立 CONTRACTS.md;契約編號 C1、C2、…)」;
  五尺度盤點微尺度格「每條領域規則」同步改「每條領域契約」。
- Skill blob hash:`e75d52754238fad495b133f9cd652b52b38365be`。
- Launch prompt:`../launch-prompt.md`(與 c1/c2 逐字同件);其餘條件同前。

## 判別性檢查(先寫死)

- **a. 節名**:SPEC 該節標題為「領域契約(Design by Contract)」
  (含 DbC 字樣的此名;純「領域規則」= 未生效)。
- **b. 編號**:契約編號為 C1、C2、…(不再是 R 系);全包交叉引用一致——
  情境、ARCHITECTURE、PROMPT、盤點凡指向該節者用 C 編號/「契約」用語,
  無殘留 R 編號或「領域規則」指稱該節。
- **c. 不另立檔**:產出仍五份,無 CONTRACTS.md。

審計注意:契約編號 C1… 與顧客編號 C001 形似,逐處按語境區分,不混計。

## 回歸檢查(逐輪累加)

- c2:ARCHITECTURE 逐條出處標記、既定逐字對賬零夾帶、自決有依據。
- c1:盤點微尺度原子性格、失敗路徑 off-script 訪談題、原子性 postcondition
  契約(枚舉失敗路徑+指名測試)。
- v2 五槽 + 舊優點(同前兩輪 pre-registration 所列)。

## 預測(輸贏以此為準)

- a、b、c 全中——純命名槽,低風險;本輪主要買的是 c1+c2 疊加後的回歸
  覆蓋(三條齊上後合約仍完整運作)。
- 最可能打折處:**b 的交叉引用一致性**——節名照改、編號照換,但正文
  某處(盤點格、PROMPT、ARCHITECTURE 依據欄)殘留「領域規則」或 R 編號
  指稱;殘留 ≤2 處記打折,節名或編號本體沒改 = c3 敗。
- 訪談深度不降:≥10 題、腳本 6/6。

## 汙染檢查(同前清單)

參考規格:`unitPriceCents`、`C-001`、`OrderListItem`;out-B2:`OrderSummary`、
`C001`;c1/c2 特徵(`PlaceOrderAtomicityTest`、`unitPriceMinor`、跑鞋/筆記本/
鋼筆、李大同/李大華)再現與否逐條判斷。python 直讀,防 rtk hook 假陰性。
注意:`C-001`/`C001` 本輪可能以「契約編號」語意自然出現,按語境判,
不自動判汙染。

## 限制

n=1;self-play 榮譽制;launch prompt 為重建件;同 model
(subagent = claude-fable-5)。
