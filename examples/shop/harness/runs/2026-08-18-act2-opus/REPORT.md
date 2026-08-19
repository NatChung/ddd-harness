# 第二幕跑通了 —— agent 交 spec,判定完全機械

**日期**:2026-08-18　**模型**:Opus 5(原生,`--safe-mode`)　**8 turns / 4.5 分 / $2.24**

## 問題

前兩個生成器是我寫的、我驗的。這次問的是:**agent 只拿散文規格 + schema,
交得出可用的結構化 spec 嗎?而且能不能不靠人讀就判定?**

## 隔離

bare dir,只有三個檔:

```
spec/SPEC.md              凍結版(4567d31)
tools/harness/schema.sql  合約
tools/harness/spec_store.py
```

**我手寫的 `acceptance.yaml`(答案卷)不在裡面**,生成器與驗收 harness 也不在。
agent 的完成定義是「`spec_store.py import` 印出 ok」——一個它自己跑得動的迴圈。

## 判定:7/7,跟我手寫的那份完全等價

```
✅ 空骨架 → 5/5 紅                     不是恆真
✅ layered/OL1-integration → 5/5 綠    可滿足
✅ S1 破壞 → 全紅(S1 被其他情境蓋住,預期內)
✅ S2/S3/S4/S5 破壞 → 只有對應那條紅
```

**我沒有讀它的 yaml 就知道它對了。** 那是 MISSION 那條「讓『對不對』不需要人來
主觀判斷」往前推了一幕 —— 原本只用在第四幕的實作,現在用在第二幕的 spec。

## 三個發現

### 1. 工具的錯誤訊息會逼出「不在指示範圍內」的產出

`_check_shape` 當時硬性要求 `architecture_rules` 非空,但指示只要求交情境。
agent 第一次 import 就撞到一個**照指示做卻過不了**的錯誤。

它的處理是**對的**:從 `SPEC.md` L55–70「領域規則」那節(該節自己寫明「與上面的
情境同等效力」)取材,六條全標 `推導自` + 行號、`enforcement: none` + `ladder_note`,
`enforced_by` 一概不寫,並在檔頭與自述裡**明說**「importer 要求此區非空」。
有來源、有標註、有揭露 —— 這不是捏造。

但**工具不該把它逼到那一步**。已修:`architecture_rules` 與 `acceptance_scenarios`
至少要有一段即可(spec 本來就是分段組成的)。

> 教訓:**完成的定義若由工具給,工具的每一條錯誤訊息就是指示的一部分。**
> 指示說「不要自己加」,工具說「這裡不能空」——衝突時 agent 會服從工具,
> 因為那是它唯一的綠燈判準。

### 2. ⚠️ 我的 schema 註解洩題

`scenario_step` 的註解當時寫著「(情境 3 送兩筆:**Alice 與 Bob**)」。

- `SPEC.md` 裡**沒有 Bob**(只有 response 範例的 `"customerName": "Alice"`)
- Bob 的真相在 `app/src/main/resources/data.sql`,**agent 拿不到那個檔**
- agent 讀了我的註解、照著填,並在自述裡誠實標明「C-002 → Bob 是照 schema.sql
  註解裡點名的補的」

**schema 註解是 agent 讀得到的東西,寫進去的具體資料值就是答案。** 已移除。

### 3. 底下藏著一個真的規格沉默

把洩題移掉之後,問題才現形:**SPEC.md 根本沒說 C-002 是誰。**
而「列表顯示顧客姓名」這條情境需要第二個顧客才證明得了姓名是 join 出來的、不是寫死的。

- 我手寫那份「知道」Bob,因為我讀了 `data.sql` —— 那是實作的 seed,不是規格
- agent 沒有那個檔,只好用我洩的註解

兩邊都在填一個規格沒寫的洞。**正確處置是讓它現形**:要嘛 spec 宣告 seed 資料,
要嘛那條情境標 `本案自決` / 規格沉默。這正是訪談 prompt 第五節在講的東西
—— 而它是被「把散文結構化」這個動作逼出來的,不是讀出來的。

## 它交的東西跟我的差在哪(都不影響判定)

- **alias 命名更好**:`singleItemOrder` / `aliceOrder`,我寫的是 `order`
- **省掉 `list_row_exists` 守衛**(S3/S4/S5):失敗時會 NPE 而不是清楚的斷言訊息。
  行為上一樣紅,訊息品質差一截。**已補成 import 期檢查 —— 而那條檢查第一件事
  就是抓到我自己**:我手寫的 S3 守了 alice 沒守 bob,而**凍結的手寫驗收也一樣
  只守 alice**,我轉寫時把那個弱點一起抄過來了。
  一條從觀察 agent 產出寫出來的檢查,同時抓到三份東西的同一個缺陷
  (agent 的、我的、最初手寫的那份)—— 這是這次跑最划算的一筆
- fixture 數值不同但合法(S4 用 2×1500 + 1×2100 = 5100,對齊 SPEC 的 response 範例)
- **沒被要求卻交了一份搬階清單**:六條 `ladder_note` 裡,A2 提議
  `archunit_forbidden_method_name` 這個新 kind、A6 指出 package 層級的依賴規則
  切不開同 package 的兩個類別 —— 後者正是我做 A10 時被逼出 `class_name_suffix`
  的同一個結構限制,它獨立撞到了
