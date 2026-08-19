# Pre-registration:spec-authoring v2 單臂驗證(寫於放 agent 之前)

日期:2026-08-12。單臂 n=1、同 model、self-play——只驗合約新槽位,不是模型實驗。

## 方法

與三臂實驗的 Arm B 逐字同條件(同腳本化 stakeholder、同工程前提、同 self-play
與禁讀規則),**唯一變因:skill 文本換成 v2 全文**(`.claude/skills/spec-authoring/SKILL.md`)。

## 檢查清單(先寫死)

**新槽位生效(五項,全數出現才算 v2 成立):**

1. SPEC 領域規則逐條有 DbC 標籤(precondition/postcondition/invariant)且分類合理,
   並逐條註明配哪個測試或為何不配。
2. 五尺度盤點出現(產出或 log 中),每尺度有落點或明寫空缺;
   **中尺度必須是「明寫空缺:本輪單 agent」**,不得跳過、不得捏造配給。
3. 「明確不在範圍」每項標來源(訪談否決 / 規格沉默)。
4. SPEC/GLOSSARY 每條規則有 [Qn] 回鏈,抽查 3 條能在 INTERVIEW-LOG 找到對應問答。
5. GLOSSARY 對金額定死單位表示法;SPEC 所有金額數字無歧義單位。

**舊優點不掉(v1 已有,回歸檢查):**

四檔全齊、GWT 真格式且 Then 可斷言、端點恰兩個、PROMPT 有凍結清單+完成定義
+ASSUMPTIONS 規則、訪談命中腳本 6/6。

## 預測

- 五項新槽全數出現;最可能打折的是(1)——postcondition 類可能貼漏
  (失敗原子性這種要 PM 自己想到),與(2)——盤點可能長成敷衍一行
  (判準:每尺度至少一行、中尺度明寫空缺才算過)。
- 訪談深度不降:≥10 題、腳本 6/6。
- 預期新增 1–2 題 off-script(DbC 標籤逼出 postcondition 類問題,
  如「下單失敗要不要留痕」)。

## 限制

n=1;self-play 洩漏同前(榮譽制+log 審計);同 model,量的是合約差不是能力差。
