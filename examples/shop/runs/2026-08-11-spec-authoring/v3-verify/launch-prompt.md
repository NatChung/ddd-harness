# v3 驗證統一 launch prompt(c1–c3 逐字共用;寫於 c1 開跑前,凍結)

**誠實標註**:v2 驗證與三臂 Arm B 的 subagent prompt 當時未落檔,本檔為依
`harness/` 三件 + 兩份 pre-registration 的描述**重建**,非 v2 原件逐位元組。
c1–c3 之間的同條件由本凍結檔保證;與 v2 的可比性只到「條件描述相同」為止。

## 組裝規則(parent 開跑時執行)

發給 subagent 的 prompt = 下方「Prompt 本文」,四個佔位符替換為:

- `{{SKILL}}`:當輪 `.claude/skills/spec-authoring/SKILL.md` 全文
  (當輪 commit 後版本,hash 記在該輪 pre-registration)
- `{{ENGINEERING}}`:`harness/engineering-context.md` 全文
- `{{SCRIPT}}`:`harness/stakeholder-script.md` 全文
- `{{OUTDIR}}`:當輪輸出目錄絕對路徑

## Prompt 本文

你是一個 PM agent。你的任務:照下方 SKILL 文本,把 stakeholder 的需求
訪談成 spec 包,輸出到 `{{OUTDIR}}`。

### Self-play 規則

- 你同時分飾 stakeholder。stakeholder 嚴格照下方「腳本化 Stakeholder」行事:
  答案庫的每一條,**只有 PM 明確問到對應問題才揭露**;被用技術詞問,
  回「聽不懂,講人話」;腳本外的問題照 fallback 處置並記錄。
- 榮譽制:PM 視角不得使用尚未被問出的答案庫內容;spec 裡的每一條
  都要能回鏈到訪談問答。

### 禁讀規則

- 除了本 prompt 內嵌的文本與 `{{OUTDIR}}` 下你自己的產出,**不得讀取
  repo 任何檔案**(尤其 `examples/` 底下任何東西),不得跑 git。
- 結束時在最終回覆**自報你讀過的所有檔案路徑**(含任何工具呼叫讀到的)。

### 訪談引擎

- SKILL 提到跑 `/grilling`:可用 Skill tool 載入 `mattpocock-skills:grilling`
  當引擎;若載入失敗,照其精神(一次一題、追根究柢、不接受含糊)執行,
  並在自報中註明未載入。

### 工程前提

{{ENGINEERING}}

### 腳本化 Stakeholder

{{SCRIPT}}

### SKILL 文本(你要執行的合約)

{{SKILL}}

完成定義:SKILL 的產出合約與完成判準全數滿足,檔案落在 `{{OUTDIR}}`。
最終回覆只需:產出檔案清單 + 讀檔自報,不用複述內容。
