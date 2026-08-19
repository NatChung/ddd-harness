# 票 16 的預測(寫在改 prompt 之前,2026-08-19)

票 16 要做的事只有一件:`run_act2.sh` 的 heredoc prompt 加第四份 `architecture.yaml`。
這份寫的是**加了之後、下一次真的跑第二幕時會量到什麼** —— 包含哪幾條交得出來、
哪幾條交不出來。

⚠️ **這份預測本票驗不了。** 驗它要花錢跑一次 `run_act2.sh`,不在本票範圍。
本票的完成 = prompt 改好 + 靜態驗過既有的 `architecture.yaml` 吃得下。
下一次跑第二幕的人請回來對這張表。

## 不用「架構規則落檔數 > 0」

那條不可能失敗 —— prompt 一旦點名 `architecture.yaml`,agent 只要交任何一條就成立。
下面每一條都寫得出「什麼結果會讓它落空」。

## 被預測的那份規格

`examples/shop/harness/runs/2026-08-19-act2/spec/SPEC.md` §9(L434–L455),R1–R10,
每條都有「由誰強制」欄,其中 8 條指名了 ArchUnit 測試名。
**注意那 8 個測試名是散文自己編的**(`LayeredArchitectureTest.layers_are_respected` 等),
不是 store 認得的 `enforcement` 值 —— store 只認四個值,而 `enforced_by` 那一欄
import 會拒收。所以「散文指名了 8 條 ArchUnit」**不等於**「落檔後有 8 條非 none」。
這正是本預測要量的落差。

## 主預測(可落空)

**§9 的 10 條裡,`enforcement` 不是 `none` 的會少於 6 條。**

落空條件:落檔後 `SELECT count(*) FROM architecture_rule WHERE enforcement <> 'none'`
回傳 **6 或以上**。

逐條的猜(比總數更容易落空,所以一起寫下來):

| # | 規則的形狀 | 猜 | 為什麼 |
|---|---|---|---|
| R1 | 分三層 package:`domain` / `application` / `infrastructure` | `none` | 「必須存在這三個 package」是「該有的東西有沒有出現」,三種 kind 都查不到。⚠️ 但**可拆**:勤快的 agent 可以只把「層間相依方向」那一面寫成 `forbidden_dependency`,那樣它會是非 none —— 這是本表最可能猜錯的一格 |
| R2 | `domain` 不得 import 框架 / 第三方 SDK | `archunit_forbidden_dependency` | 跟現成 `architecture.yaml` 的 A1/A2 同型,最典型的一條 |
| R3 | 依 §1.1 切五個 context package | `none` | 「叫這個名字的東西必須住在這裡」需要 `required_location` 這種不存在的 kind |
| R4 | `ordering` 不得直接 import `inventory` 的領域型別 | `archunit_forbidden_dependency` | 兩個 package 之間的禁止依賴,正中 kind |
| R5 | 相依方向單向 **+** `reporting` 只讀不回寫 | `none` | 票裡點名的三條之一。「只讀」是行為,不是依賴。⚠️ 前半(方向)可拆成 `forbidden_dependency`,拆了就變非 none —— 第二可能猜錯的一格 |
| R6 | 聚合根只以識別碼引用外部,不持有對方物件 | 不確定 | 寫成 package 層級的禁止依賴的話會跟 R4 重複;寫成類別層級則需要不存在的 kind。**這一格我不押** |
| R7 | 第三方支付以 port 表達,領域層只認識介面 | `archunit_forbidden_dependency` | 可寫成「domain 不得依賴任何支付廠商 package」;但廠商 package 名散文沒給(A-13 說沒指定廠商),agent 可能因此改標 `none` |
| R8 | 每月銷量走獨立讀模型,不得載入聚合根加總 | `none` | 散文自己就寫「目前無機械檢查(第 4 階)」 |
| R9 | 一次交易只改一個聚合根 | `none` | 同上,散文自己標了第 4 階 |
| R10 | 購物車型別 / package / 欄位一律不得存在 | `none` | 「某個名字的東西不得存在」不是依賴、不是 annotation、不是回傳型別 |

押注的非 none:**R2 / R4 / R7 三條**,最多再加 R6 →
**3 到 4 條**,所以「少於 6」有餘裕。落空的路徑是 agent 把 R1 與 R5 拆半交出,
那樣就是 5 或 6,**剛好踩線** —— 若真的量到 6,主預測落空,而那是好事:
表示 agent 比我預期的更會拆規則,不是 prompt 壞了。

## 副預測(兩條,都可落空)

1. **`authorized_templates` 會是空的**(`[]` 或整個 key 沒交)。
   落空條件:落檔後 `SELECT count(*) FROM authorized_template` 非 0。
   依據:那份 SPEC 的 §9 開頭與卷首都寫著「本案沒有被授權為架構模板的文件(`[Q5]`「沒有」)」。
2. **`provenance = '模板既定'` 零筆。**
   落空條件:`SELECT count(*) FROM architecture_rule WHERE provenance='模板既定'` 非 0。
   注意這一條**其實不可能只是「沒發生」** —— 白名單空的時候 schema 的
   `template_provenance_must_be_authorized` trigger 會 ABORT,整份 import 掛掉。
   所以它真正的落空形式是:**agent 交了模板既定 → import 紅 → agent 改掉再交**,
   最終落檔仍是零筆,但過程中撞過牆。那個過程在 `result.json` 裡看得到。
   ⚠️ 歷史上模型兩輪都把自決偽裝成既定,所以這條的價值不是「會不會零筆」,
   而是**它現在是靠 trigger 而不是靠自覺守住的**。

## 這份預測**不**主張的事

- **不主張 §9 的 10 條會全數落檔。** agent 可能合併或漏掉。
- **不主張生成出來的 ArchUnit 會抓到東西。** 第三幕的實作若沒有那些 package,
  `allowEmptyShould(true)` 會讓它們必然綠 —— 那是票 10 的坑,不是這裡。
- **不主張非 none 的那幾條會生得出可編譯的 Java。** `gen_archunit` 吃得下形狀,
  不代表 package 名對得上實作。

## 已知上限(不是預測,是事實)

**交得出來 ≠ 生得出來。** `gen_archunit` 只吃三種 kind
(`forbidden_dependency` / `forbidden_annotation` / `forbidden_return_type`)。
形狀不在那三種裡的規則,**正確的落檔結果就是 `enforcement: none` + `ladder_note`**。
落檔後看到好幾條 none,那是對的,不是 prompt 沒寫清楚 —— 不要為了讓數字好看去湊。
