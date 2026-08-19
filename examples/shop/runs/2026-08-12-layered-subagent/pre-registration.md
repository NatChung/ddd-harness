# Pre-registration:分層 subagent 管線實驗(寫於放任何 agent 之前)

日期:2026-08-12。依 `DESIGN.md` 凍結;逐洞預測表**逐字照抄** DESIGN 末節,
本檔另補操作化細節。凍結後不改;與產出對賬寫進 REPORT.md。

## 樣本與模型

| 樣本 | 模型(三層同模型) | 分支前綴 |
|---|---|---|
| OL1 | Opus 5(Agent tool `model: opus`) | `layered/OL1-` |
| HL1 | Haiku 4.5(`model: haiku`) | `layered/HL1-` |
| HL2 | Haiku 4.5(`model: haiku`) | `layered/HL2-` |

對照組 = 輪 1 現成 O1/O2/H1b/H2b(同 spec、同骨架、同模型、單 agent)。
**樣本間並行、樣本內三層依依賴方向串行**(domain → usecase → adapter;
DESIGN 的「不並行」指樣本內的層,樣本間彼此獨立)。

## 工作區機制(讀=物理缺席、寫=git 作證)

- 每層一個 worktree,base = 骨架 `4567d31`;分支 `layered/<樣本>-<層>`。
- **Parent 先 commit 一個 `setup:` 裁檔 commit**(刪不配給的檔案)再放 agent
  ——農場乾淨房間;收件 diff 以 setup commit 為基準,setup 的刪除天然不進 merge。
- Agent 產出以 git commit 交件(訊息前綴 `impl(<層>):`);收件驗 commit
  祖先=setup commit、白名單 diff、parent 親跑測試,不採信自報。

### 裁檔清單(操作化;DESIGN 配給表的逐檔展開)

**共通刪除(三層皆刪)**:repo 頂層除 `.gitignore`、`examples/` 外全刪
(`.claude/ .mcp.json .scratch/ CLAUDE.md CONTEXT.md MISSION.md NOTES.md
README.md RESOURCES.md assets/ brain-archive/ docs/ learning-records/
lessons/ practice/ reference/ tools/`);另刪 `examples/shop/README.md`
(含實驗性質描述)。

| 層 | 另刪 | 留下 | 可寫白名單(diff 檢查依此) |
|---|---|---|---|
| domain | `spec/PROMPT.md`、`app/src/test/java/acceptance/`、`app/src/main/resources/`、`app/src/main/java/com/shop/Application.java` | spec 三份(SPEC/GLOSSARY/ARCHITECTURE)、build 檔+wrapper、`ArchitectureTest.java`、`com/shop/domain/` 空目錄(parent mkdir) | `app/src/main/java/com/shop/domain/`、`app/src/test/java/com/shop/domain/`、`app/ASSUMPTIONS.md`、`app/INTERFACE-REQUESTS.md` |
| usecase | 同 domain | 同 domain + **domain agent 通過收件的 `domain/` 原始碼與其單元測試**(唯讀) | 同型,換 `usecase/` |
| adapter | 只做共通刪除 | 全部:spec 四份、驗收測試、resources、`Application.java`、內兩層原始碼與測試 | `app/src/main/java/com/shop/adapter/`、`app/src/test/java/com/shop/adapter/`、`app/src/main/resources/`、`app/ASSUMPTIONS.md`、`app/INTERFACE-REQUESTS.md` |

註 1:`Application.java` 對 domain/usecase 刪除是本檔的操作化決定(DESIGN 未
列;它 import Spring,內層不需要)。註 2:`ArchitectureTest.java` 三層都留
(機械檢查屬 build 檔精神,ArchUnit 對缺席的層 vacuous 通過)。註 3:adapter
可寫 resources 照 DESIGN 配給表;其對 harness 檔(data.sql 等)的任何改動
收件時 parent 逐行目檢並記錄。

## INTERFACE-REQUESTS 協定(照 DESIGN)

白名單外的任何需求:唯一合法動作 = 寫 `app/INTERFACE-REQUESTS.md`
(要什麼、為什麼)、commit、停下回報 blocked。Parent 裁決:駁回給替代做法
(以 SendMessage 續跑同一 agent),或開票給擁有層 agent。全部留檔,
內容本身是主要量測物。

## 完成定義(per 層)與紅燈路由

- domain / usecase:`./gradlew test` 綠(= 自己的單元測試 + ArchUnit;
  各層 prompt 帶自驗要求——**prompt 效果,非隔離效果,結論綁定標註**)。
- adapter:`./gradlew test` 全綠(驗收 + ArchUnit + 全部單元測試)。
- 整合:parent 開 `layered/<樣本>-integration` worktree(base 同,不裁檔),
  以 `git checkout <層分支> -- <白名單路徑>` 按層合併,親跑 `./gradlew test`。
- 紅燈:parent 判歸屬層,把失敗輸出原文發回該層 agent(原 worktree、配給
  不變),**每層最多 2 輪修復**;仍紅 = 該樣本記失敗,原樣入報告。
- 越界(白名單外 diff 非空):整包退件令其重做,退件次數入報告。

## 量測(主指標在前;照 DESIGN)

1. 逐洞比對:H1b/H2b 的 review 洞在 Haiku-layered 樣本中存在與否。
2. INTERFACE-REQUESTS 內容與 parent 裁決記錄。
3. 越界退件次數、修復輪數、(參考)token 成本。
4. 通過率預期無差異,不是指標。

兩軸 review 照輪 1 規格(Standards 軸 = ARCHITECTURE+GLOSSARY+Fowler
baseline;Spec 軸 = SPEC.md;reviewer 全 Opus、唯讀、互不見彼此;ArchUnit
已強制者不報):3 樣本 × 2 軸 = 6 reviewer。

## 逐洞預測(逐字照抄 DESIGN 末節,凍結)

| 洞(輪 1 review) | 預測 | 機制 |
|---|---|---|
| 🔴 H2b public 建構子後門 | **消失** | 寫隔離:後門須經 INTERFACE-REQUESTS,domain agent 依規格駁回;且 domain agent 不知 JPA,誘因被拆 |
| 🔴 H2b 幣別檢查可跳過 | 再現(不解) | domain 內部邏輯品質,與邊界無關 |
| 🟠 addItem 失敗不原子 | 再現(不解) | 契約層,輪 2 候選 4 的地盤 |
| 🟠 INNER JOIN 掉單 | 再現(不解) | 驗收射程外,輪 2 候選 3 的地盤 |
| 🟡 壞死碼毀 placedAt | 不押注,列觀察 | 注意力假說(context 窄→雜訊少),證據不足 |
| 🟡 捏造 ASSUMPTIONS | 再現(不解) | 誠實性問題,靠收件重驗 |
| 零自發測試(Haiku) | 部分改善 | 配給裡各層帶自驗要求——**prompt 效果,非隔離效果**,綁定標註 |

**總預測一句**(照抄):分層只消「跨層便利性妥協」類;若結果如此,結論是
「分層 subagent 與『沉默處變規則』(輪 2)正交——一個管過程、一個管規格,
互不替代」。

## 誠實標註(先認)

- Treatment = 「隔離 + per-layer prompt」**綁在一起**,無法拆分歸因。
- 三層 prompt 是新增檔案(`prompts/`),不進 `spec/`;`spec/` 與 `app/`
  骨架逐位元組停在 `4567d31`。
- Agent 有 git 可用(交件需要);禁讀其他 ref 靠 prompt 條款+自報,無硬隔離
  ——與輪 1 同級的榮譽制殘餘。
- 每 agent 記錄:model、退件次數、修復輪數、是否觸發 INTERFACE-REQUESTS。
