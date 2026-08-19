# 分層 subagent 管線實驗 —— 設計稿(未開跑)

日期:2026-08-12。狀態:**規則已定,等 Nat 說開跑**。開跑前先把本檔末節凍結成 pre-registration。

## 問題

單 agent 實作(輪 1 的 O1/O2/H1b/H2b)在規格沉默處長出的洞,有哪些能被
「分層 subagent + context/寫權限隔離」消掉?尤其:H2b 的 public 建構子後門
(跨層便利性妥協)是否在分層下無法形成?

## 鐵律遵守聲明

- `spec/` 四份與 `app/` 骨架**逐位元組不動**,維持 `4567d31` 的內容——
  K3/MiniMax 的受控輸入不受影響。
- 分層臂的三份 per-layer prompt 是**新增檔案**,活在本 run 目錄,不進 `spec/`。
- 誠實標註:分層臂的 treatment 是「隔離 + per-layer prompt」**綁在一起**的,
  無法只隔離不換 prompt;結論措辭要照這個綁定寫。

## 拓撲與順序

```
parent(orchestrator:發包、收件、裁決,不寫 code)
└── domain agent → usecase agent → adapter agent(依依賴方向串行)
```

不並行(並行需要骨架先給介面=動骨架,違反鐵律;串行版介面由 domain/usecase
自己長,與單 agent 對照組條件更接近)。

## 配給表(讀=乾淨房間,物理缺席)

每個 agent 一個 worktree(base 驗過 = 骨架 commit),launch 前 **parent 先
`rm -rf` 掉不配給的檔案**——讀不到不存在的東西。收件只取白名單路徑的 diff,
setup 的刪除不進 merge。

| Agent | 配給(留下的檔案) | 刪掉(物理缺席) | 可寫白名單 |
|---|---|---|---|
| domain | GLOSSARY、SPEC(領域規則節為主,全文亦可)、build 檔、`domain/` 空包 | ARCHITECTURE 的持久化節?**否——整份 ARCHITECTURE 留**(相依規則它該知道);刪:驗收測試、`resources/`(data.sql 等)、usecase/、adapter/ | `app/src/main/java/com/shop/domain/` + 自己的單元測試 `app/src/test/java/com/shop/domain/` |
| usecase | 上述 + domain agent 產出的 `domain/` 原始碼(唯讀=不在可寫白名單) | 驗收測試、`resources/`、adapter/ | `.../usecase/` + `.../test/java/com/shop/usecase/` |
| adapter | 全部(它是最外層):spec 四份、驗收測試、resources、內兩層原始碼 | 無 | `.../adapter/` + `resources/` + `.../test/java/com/shop/adapter/` |

## 寫權限:收件驗 diff(機械,第 2 階)

每包收件時 parent 跑:

```bash
git diff --name-only <base>..<head> | grep -vE '^(白名單路徑)' 
```

輸出非空 = 越界,**整包退件**(記錄後令其重做,退件次數入報告)。
另沿用輪 1 定案的收件程序:驗 commit parent、不採信自報、parent 親跑測試。

## INTERFACE-REQUESTS 協定(洞現形機制)

agent 需要**白名單外**的任何改動(如 adapter 想要 domain 加建構子):唯一合法
動作是寫入自己 worktree 的 `INTERFACE-REQUESTS.md`(要什麼、為什麼)然後停下。
parent 裁決:駁回(給替代做法)或開票給擁有層的 agent。**全部留檔**——這份
檔案的內容本身就是主要量測物之一。

## 整合與紅燈路由

parent 把三包按層合併進整合 worktree → `./gradlew test` 全套(驗收+ArchUnit)。
紅燈時:parent 判斷歸屬層,把**失敗輸出原文**發回該層 agent 修(在其原 worktree,
配給不變),**每層最多 2 輪修復**;仍紅=該樣本記為失敗,原樣入報告。

## 樣本與對照組

- 分層臂:Opus-layered ×1、Haiku-layered ×2(效果預測在 Haiku 側,雜訊底線
  沿用輪 1 的同型雙樣本邏輯)。
- **對照組=輪 1 現成的 O1/O2/H1b/H2b**(同 spec、同骨架、同模型、單 agent)。
- 兩軸 review 照輪 1 規格對分層樣本重跑,才能逐洞比對。

## 量測(主指標在前)

1. **逐洞比對**:H1b/H2b 的 review 洞在 Haiku-layered 樣本中存在與否。
2. **INTERFACE-REQUESTS 內容**:出現了什麼請求、parent 裁決記錄——單 agent
   模式下不可見的資料。
3. 越界退件次數、修復輪數、(參考)token 成本對比。
4. 通過率:預期無差異(全綠),不是指標。

## 逐洞預測(開跑前凍結;判準:該洞在分層 Haiku 樣本是否再現)

| 洞(輪 1 review) | 預測 | 機制 |
|---|---|---|
| 🔴 H2b public 建構子後門 | **消失** | 寫隔離:後門須經 INTERFACE-REQUESTS,domain agent 依規格駁回;且 domain agent 不知 JPA,誘因被拆 |
| 🔴 H2b 幣別檢查可跳過 | 再現(不解) | domain 內部邏輯品質,與邊界無關 |
| 🟠 addItem 失敗不原子 | 再現(不解) | 契約層,輪 2 候選 4 的地盤 |
| 🟠 INNER JOIN 掉單 | 再現(不解) | 驗收射程外,輪 2 候選 3 的地盤 |
| 🟡 壞死碼毀 placedAt | 不押注,列觀察 | 注意力假說(context 窄→雜訊少),證據不足 |
| 🟡 捏造 ASSUMPTIONS | 再現(不解) | 誠實性問題,靠收件重驗 |
| 零自發測試(Haiku) | 部分改善 | 配給裡各層帶自驗要求——**prompt 效果,非隔離效果**,綁定標註 |

**總預測一句**:分層只消「跨層便利性妥協」類;若結果如此,結論是「分層 subagent
與『沉默處變規則』(輪 2)正交——一個管過程、一個管規格,互不替代」。

## 待寫(開跑時)

三份 per-layer prompt(自足、含 self-play 無、含白名單與 INTERFACE-REQUESTS
規則)、pre-registration 凍結檔、parent 收件 checklist。
