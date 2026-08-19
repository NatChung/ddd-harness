# c1 驗證報告(評分依本目錄 pre-registration.md,清單未改動)

日期:2026-08-12。評審:主 session 逐檔讀 out/ 五份原文 + [Qn] 抽查 + python
汙染 grep,不採信自報。subagent model:claude-fable-5(繼承主 session)。

## 結論一句

**c1 成立**:判別性三項全中——v2 靠 PM 自己想到才有的失敗原子性,c1 由
盤點檢查句逼成訪談問題(Q9)→ 契約(R8 postcondition)→ 每條失敗情境的
Then 斷言,整條鏈可回鏈。回歸零損失。v2 殘洞 2(出處誤標)**原樣再現**,
留作 c2 的活靶。

## 判別性三項對賬

| # | 檢查 | 結果 |
|---|---|---|
| a | 盤點格生效 | ✅ 五尺度盤點微尺度格含原子性判準,結果具體(R1–R9 全標 + 指明 R8 覆蓋 S3–S8),非照抄檢查句 |
| b | 訪談現形 | ✅ Q9「下單到一半系統出錯,會不會看到半張訂單?」——白話、走 fallback-業務、PM 建議(全有全無)被記錄;正是 v2 pre-reg 預測該出現而沒出現的那類問題 |
| c | 落到契約 | ✅ R8 postcondition,失敗路徑逐項枚舉(R2–R5 違反、幣別格式錯、持久化中途失敗);配 `PlaceOrderAtomicityTest`(=S8);S3–S7 每條 Then 各自斷言「訂單數不變、無 OrderLine 落地」。讀端點無寫入,照 pre-reg 邊界條款無原子性義務 |

亮點:S8 的 test double 設計成「**部分寫入完成後才失敗**」並在 Given 明寫
理由(防止測試因什麼都沒寫而空洞通過)——超出合約要求的自發品質
(agent 自報為其 advisor 覆核後所改)。

## 回歸(v2 五槽 + 舊優點)

全過:R1–R9 全標 DbC 且分類合理(R6 不配測試附「型別結構不可表示」的好
理由);盤點中尺度明寫空缺:本輪單 agent;不在範圍 11 項逐項標來源、收尾
「不要做」;[Qn] 抽查 R3→Q10、R7→Q7、R9→Q1/Q5/Q13 全對上;金額 cents
整數全線無歧義(2500/5000/3400)。五檔齊、GWT 具體可斷言、端點恰兩個、
PROMPT 凍結清單+完成定義(指名測試逐一列出)+ASSUMPTIONS 規則、
腳本 6/6 命中(Q1–Q7)、技術詞打槍 fallback 觸發(Q12→Q13 改口)。
訪談 14 題(v2 為 17,≥10 門檻過)。

## 預測對賬

| 預測 | 結果 |
|---|---|
| a 幾乎必中 | 贏 |
| 真考驗在 b,預測逼出 ≥1 題失敗路徑 off-script | **贏**——Q9 正中 |
| c 最可能打折:漏持久化失敗這類 PM 想不到的路徑 | 輸(輸得好)——持久化失敗不但列入,測試設計還防了空洞 |
| 訪談深度 ≥10、腳本 6/6 | 贏(14 題、6/6) |

## 觀察(不計分)

1. **v2 殘洞 2 原樣再現(c2 的靶)**:ARCHITECTURE「常備模板(starter,
   原樣沿用)」節寫「Repository 介面宣告在 domain,JPA 實作在 adapter
   (依賴反轉)」——工程前提從未給過這條,與 v2 同一句自決偽裝成既定。
   c1 不修不扣分,但證明洞仍活著,c2 修法有明確可消對象。
2. 小瑕:A3 引「GLOSSARY 命名鐵律(`unitPriceCents`/`totalCents`)」,
   但 GLOSSARY 鐵律表列的是 `UnitPrice`/`TotalAmount`(欄位級 JSON 名只
   出現在 SPEC 形狀)——引用不精確,量級小。

## 汙染檢查(python 直讀,防 rtk hook 假陰性)

- 參考規格(4567d31)token:`C-001` 0、`OrderListItem` 0、
  **`unitPriceCents` 出現**(SPEC×5、ARCHITECTURE×1)。判定:灰色偏自然
  ——skill 文本例句「金額一律 cents 整數」+ JSON 欄位命名慣例可直接導出,
  且另外兩個參考特徵均未伴隨;v2 同一例句下選了 minor units,屬同分佈
  內變異。記錄在案,不判偷看。
- out-B2 token:`OrderSummary` 0、`C001` 出現(顧客編號 C001 為高自然度
  選擇,「王小明」同見於 out-B2)——同型模型自然趨同,self-play 榮譽制
  限制照舊。
- agent 自報:零 Read、未跑 git;grilling 經 Skill tool 載入(注入文本,
  非讀檔)。

## 限制

n=1;self-play 榮譽制;launch prompt 為重建件(見 ../launch-prompt.md);
同 model 無跨模型效度。
