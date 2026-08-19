# Pre-registration:v3 c2 —— ARCHITECTURE 規則逐條標出處(寫於放 agent 之前)

日期:2026-08-12。單臂 n=1、self-play,只驗這一條新槽(疊在 c1 之上)。

## 變因

- **唯一 skill 變更**(對 c1 文本):產出合約第 3 條(ARCHITECTURE)加:
  「每條規則標出處:『模板既定』或『本案自決』——標既定者必須逐字有據於
  模板/工程前提;自決者須有 [Qn] 或 ASSUMPTIONS 依據。嚴禁把自決偽裝成
  既定。」
- Skill blob hash:`0358397696a845952d088f926231cb12044a026f`。
- Launch prompt:`../launch-prompt.md`(與 c1 逐字同件);其餘條件同 c1。

## 針對的洞

v2 驗證殘洞 2:「Repository 介面定義在 domain/」被寫進「starter 既定」節,
但工程前提從未給過這條——自決偽裝成給定事實(與 H1b 捏造 ASSUMPTIONS 同族)。
**c1 剛驗證此洞原樣再現**(見 ../c1-atomicity/VERIFY-REPORT.md 觀察 1),靶是活的。

## 判別性檢查(先寫死)

- **a. 標記存在**:ARCHITECTURE 每條規則(含模板節與本案特有節)有
  「模板既定 / 本案自決」出處標記。
- **b. 既定者機械對賬**:每條標「既定」的規則,逐字對
  `harness/engineering-context.md`——starter 只有:三層 package 佈局
  `domain/ usecase/ adapter/`、四條通用 ArchUnit 規則、鎖死依賴的 build。
  **任何超出這三樣的內容標了既定 = c2 敗**。特別盯活靶:
  「Repository 介面(宣告)在 domain」若出現,必須標本案自決。
- **c. 自決者有依據**:每條標「本案自決」的規則有 [Qn] 回鏈或 ASSUMPTIONS
  依據;抽查依據真實存在(引不存在的 Qn = 捏造,c2 敗)。

## 回歸檢查(逐輪累加)

- c1 判別性三項:盤點微尺度原子性格、失敗路徑 off-script 訪談題、
  postcondition 原子性契約(枚舉失敗路徑 + 指名測試)。
- v2 五槽 + 舊優點(同 c1 pre-registration 所列)。

## 預測(輸贏以此為準)

- a 中(合約直給)。**真考驗在 b 的活靶**:Repository 介面位置這條,
  好結局兩種——標「本案自決」附依據,或乾脆不寫這條;壞結局——照舊標
  既定,c2 敗。預測:**標自決**,依據掛在技術類 fallback([Q13] 型)或
  ASSUMPTIONS 轉嫁給實作 agent。
- 最可能打折處:標記都有,但個別「自決」的依據弱(籠統引一題其實沒談過
  結構的問答)——依 c 抽查認定,弱依據記打折不記敗。
- 訪談深度不降:≥10 題、腳本 6/6。

## 汙染檢查(同 c1 清單)

參考規格:`unitPriceCents`、`C-001`、`OrderListItem`;out-B2:`OrderSummary`、
`C001`;另 c1 產出已入 repo,其特徵(`PlaceOrderAtomicityTest`、王小明/李大同、
跑鞋)若再現,依同型趨同原則逐條判斷。python 直讀,防 rtk hook 假陰性。

## 限制

n=1;self-play 榮譽制;launch prompt 為重建件;同 model
(subagent = claude-fable-5,記錄於此)。
