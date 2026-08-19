# Pre-registration:spec-authoring 三臂實驗(寫於放 agent 之前)

日期:2026-08-11。單次運行(n=1/臂)、同 model 三臂、self-play。

## 問題

什麼樣的 prompt/skill 能把「stakeholder 一句需求」訪談成
examples/shop/spec 那種形狀的 spec 包?裸的 grill-with-docs 夠不夠?

## 三臂

- **Arm 0(對照/shape-only)**:直接給完整訪談逐字稿(答案全揭露),
  要求「為 AI 實作 agent 產出規格文件」,**不給任何格式合約**。
  測的是:沒有輸出合約時,自然長出什麼形狀。
- **Arm A(grill-with-docs 原樣)**:grilling + domain-modeling(含兩份
  FORMAT 檔)逐字餵入,self-play 訪談腳本化 stakeholder,照 skill 交付。
- **Arm B(薄 spec-authoring skill)**:grilling 當引擎 + 四檔輸出合約。

受控變因:需求原句、答案庫、fallback 規則、工程前提 blurb 三臂逐字相同;
禁讀 repo 檔案(尤其 examples/)+ 要求自報讀過的檔案。

## 評分 rubric(先寫死,看產出前不改)

- **R1 決策覆蓋**:六條決策(成立鎖定/顧客在邊界外/幣別不混/列表四欄+
  「已成立」中文/取消改單不做/總額系統算)各:有沒有被問到?落檔在哪?
- **R2 GWT 品質**:行為是否寫成 Given-When-Then;每條 Then 可斷言、
  可一比一翻成自動化測試。
- **R3 「明確不在範圍」槽位**:存在、逐項列、收尾「不要做」等級的硬話。
- **R4 命名紀律**:標準 DDD token(Aggregate Root/Value Object/Repository);
  有「不得另創同義詞」等級的鐵律。
- **R5 結構決策落點**:Repository 介面在 usecase、View Model 在 usecase、
  持久化模型與領域物件分離——有沒有被寫出來。
- **R6 工作契約**:PROMPT 等級的東西(凍結清單、完成定義=測試全綠、
  ASSUMPTIONS 機制)存不存在。
- **R7 訪談品質**(A/B 臂):INTERVIEW-LOG 問了幾題、命中腳本幾條、
  off-script 處置是否照 fallback。

## 預測(輸贏以此為準)

- **Arm 0**:R1 高(答案是餵的,不算本事)。判別器在槽位:預測 **缺 R3
  硬結尾、缺 R6**;R2 部分散文化;可能自行展開範圍(分頁/查單筆之類)。
- **Arm A**:R7 好、R4 的 glossary 好(CONTEXT.md 格式自帶 Avoid 欄);
  1–3 條 ADR,「取消不做」可能以 ADR 的 no-s 形式被接住一部分。
  預測 **缺 R2(domain-modeling 明文 CONTEXT 不是 spec)、缺 R3 槽位、
  缺 R6**。
- **Arm B**:R1–R6 形狀齊。風險:GWT 前提資料不夠具體(R2 打折)、
  訪談比 A 淺(合約壓力導向填格子,R7 打折)。

## 已知限制(先認)

- self-play 洩漏:同一 context 拿著答案庫,「沒問到就不知道」靠榮譽制
  + log 審計,防不了真偷看。
- n=1、同 model:量的是 skill 合約的形狀差,不是模型能力差。
- 禁讀 repo 靠指令 + 自報,無硬隔離。
