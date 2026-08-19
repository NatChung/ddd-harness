# 10 — 把骨架擴充成「服務訪談那份規格」的骨架

**What to build:** 從 `examples/shop/app/` 複製一份改,補齊訪談那份規格 §10 點名的東西,
並把骨架納入受測品紀律。

**Blocked by:** None(做法已定,見 `docs/adr/0006` §2、§6)

**Status:** **done**(2026-08-19)—— `examples/shop/app-from-interview/`(15 檔)。空骨架實測:驗收 12/12 紅(runtime,兩類)、架構 4/4 綠但命中 0 個 class → 記「不適用」。外部替身未做(這份規格的情境不需要,三個獨立證據見 `10-RESULT.md`)。⚠️ P4 落空:`verify_generated.py` 對這份 store 整支 crash → 已由票 14 修掉。

## 差額(現有骨架 vs §10 要的)

| | 現有 | §10 要的 |
|---|---|---|
| 測試套件 | 2 套,而且是**凍結那份規格**的 | 3 套:`PlaceOrderAcceptanceTest` / `OrderListAcceptanceTest` / `ArchitectureRulesTest` |
| 外部替身 | **無**(`data.sql` 的 `customers` 表勉強算一半) | 兩支,要能模擬查無此人 / 查無此商品 / **逾時** |
| package | `com.shop.domain` / `com.shop.usecase` | `order/domain` / `order/application` / `order/adapter` |
| wire 欄位 | `orderId` / `customerName` / `statusLabel` / `totalCents` / `placedAt` | 整組不同(見該份規格的「端點」章節) |


## ⚠️ 目標是哪一份規格 —— 派工時才發現要先講清楚

**有兩份訪談產出的規格,而只有一份跑得起來:**

| 規格 | 落檔了嗎 | 生成的測試 | §10 內容 |
|---|---|---|---|
| `runs/2026-08-18-act2-from-interview/input-SPEC.md` | ✅ **12/12**(`act2-rerun/agent-acceptance.yaml`) | ✅ `act2-rerun/generated-OrderAcceptanceTest.java`(16 個 @Test)+ Proxy 那支 | 較早、較簡單 |
| `runs/2026-08-18-act1-opus-rerun/SPEC-draft.md` | ❌ **一條情境都沒落檔** | ❌ 沒有 | 三套測試 + 兩支外部替身 + 逾時 |

**定案:骨架做給有 store、有生成物的那一份**(`act2-rerun`)。
理由很笨但擋不掉:**測試生不出來的規格,骨架做了也跑不起來。**

所以本票的 §10 那張差額表要這樣讀:三套測試 / 兩支外部替身 / 逾時,
**是另一份(還沒落檔的)規格要的**。它們不是本票的交付,是**記下來的缺口** ——
等那份規格走完幕二、生得出測試,才輪到補。

**本票實際要做的**:讓 `act2-rerun` 那份生成物**跑得起來** ——
build 檔、啟動點、測試資料、空的實作 package、把兩支生成的 class 放對位置。
外部替身**這一份用不用得到,實作前先確認**(它的情境裡有沒有需要外部系統回失敗的);
用不到就不要做,並在報告裡明講「HTTP 假服務未做,因為這份規格的情境不需要」。

## 硬約束(ADR 0006)

- **外部替身是 HTTP 假服務,站在進程外。** 不准宣告任何 Java port 介面給 agent 照著實作
  —— 那會打破「測試不 import 任何實作 class」,而那是整條線判定得了兩份實作的根據。
- **三個實作 package 建空目錄**,型別一個都不給。
- **架構那套保留 `allowEmptyShould(true)`**,但空骨架階段要被報成「**不適用**」,不是通過。
- **骨架是受測品**,三條紀律:檔頭警語(照 `run_act2.sh`)/ 每跑留快照或 blob 雜湊、
  寫報告前 diff / 洩題面列清單(哪些檔 agent 讀得到、哪些值是答案卷)。

⚠️ **洩題面比 schema 註解大得多** —— `data.sql`、`application.properties`、
假服務的回應內容都是 agent 讀得到的具體值。

⚠️ 先寫預測,commit 在實作之前,而且預測要挑得出哪個結果會讓它落空。
