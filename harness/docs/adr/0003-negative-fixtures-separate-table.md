# ADR 0003 — 負面情境的 fixture 走另一張寬鬆的表,用 FK 綁住「只有預期被拒的情境才掛得上」

## Status

Accepted(2026-08-18)

## Context

`harness/schema.sql` 的立基(輪 2 重談第 3 題)是「**填不了就寫不進去**」——
schema 的 CHECK 讓不合法的 spec 資料寫不進 store,這比事後 review 早一步、而且是機械的。

2026-08-18 把第一幕訪談產出的散文規格餵進第二幕,量到一件在凍結那份規格上**永遠量不到**
的事:12 條情境進去,只有 4 條落得了檔。擋住其中最多條的是這個:

```sql
CREATE TABLE step_item (
    quantity INTEGER NOT NULL CHECK (quantity > 0),   -- ← 擋掉 S5「數量 0 要拒絕」、S6「數量負數要拒絕」
    ...
);
```

> **schema 的 CHECK 是為了「讓不合法的資料寫不進去」而設的。
> 而負面情境的 fixture,本質上就是不合法的資料。**

同一條 CHECK 同時擋掉兩種東西:手滑寫錯的規格,和「數量必須 ≥ 1」這條規則的**驗收**。
**守衛與覆蓋率互相扣分。** 凍結的 `examples/shop/spec/SPEC.md` 那 5 條情境裡一條負面情境
都沒有,所以這個衝突在它身上不存在;而訪談問出來的 12 條裡有 5 條是拒絕情境
——**這正是訪談最會問出來的類別。**

根源比「CHECK 太嚴」更深:`scenario_step` 被建模成**一筆訂單**(領域值),但驗收情境打的
是**邊界**,而邊界收得到領域永遠不會持有的東西。客戶端**可以**送數量 0、送空單、沒登入、
夾帶假總額;領域一個都不能持有。

順帶查證到:守衛其實住在兩層,只有一半是 schema —— S4(空單)是被
`harness/spec_store.py:227` 的 Python 擋的,不是 CHECK。

## Considered Options

- **A 另開一張寬鬆的表**,欄位與 `step_item` 重複一份,各自 CHECK 嚴格。
- **B 就地拿掉 CHECK,把守衛搬到 importer**(檢查「違法值 ⇔ 該情境斷言拒絕」)。
- **C 同一張表加 `expect_rejected` 布林 + 條件式 CHECK。**
- **D(採用)寬鬆的表 + 用 FK 綁住「只有預期被拒的情境才掛得上」。**

## Decision

**採 D。** `acceptance_scenario` 增一欄 `expects_rejection`,並對 `(id, expects_rejection)`
開 UNIQUE;負面請求的表 FK 指那一對,自己 CHECK 該欄恆為 1。

```sql
CREATE TABLE acceptance_scenario (
    id                TEXT PRIMARY KEY,
    expects_rejection INTEGER NOT NULL CHECK (expects_rejection IN (0,1)),
    ...
    UNIQUE (id, expects_rejection)        -- 讓子表 FK 得到這一對
);

CREATE TABLE rejected_request_item (
    scenario_id       TEXT NOT NULL,
    expects_rejection INTEGER NOT NULL CHECK (expects_rejection = 1),
    quantity          INTEGER NOT NULL,   -- 刻意沒有 quantity > 0
    ...
    FOREIGN KEY (scenario_id, expects_rejection)
        REFERENCES acceptance_scenario(id, expects_rejection)
);
```

決定前實測過這個 FK 技巧在 SQLite 真的成立,不是設計上覺得可以:

```
✅ S5 quantity=0 寫得進去(預期被拒的情境)
✅ S1 預期成功卻掛違法請求:被擋 —— FOREIGN KEY constraint failed
✅ 不存在的情境:被擋 —— FOREIGN KEY constraint failed
```

## 為什麼不是另外三個

- **C 是 schema 自己的註解點名要避開的東西。** `schema.sql:88` 寫著:「塞成一張表加一個
  kind 欄位,就得把 CHECK 寫成條件式 —— 那是『schema 表達不了』的開端」。照 C 做等於推翻
  自己記下來的教訓。
- **B 把守衛移出 schema,而那正是第 3 題買的東西。** 而且它會讓「Python 擋的那半」從一半
  變成全部。
- **A 能用,但守衛只擋得住「值違法」,擋不住「預期成功的情境卻掛了違法請求」** —— 而那才
  是真正會出事的誤用(把 1 打成 -1,情境卻斷言 201)。D 多擋住這一種,而且是**宣告式的**,
  不用寫任何檢查程式碼。
- D 與既有先例一致:三個 archunit rule kind 就是三張表,理由同一條(參數不同、CHECK 不同)。

## Consequences

- **欄位會重複一份。** `rejected_request_item` 的欄位與 `step_item` 幾乎相同,只差沒有
  CHECK。這是刻意付的代價,換「不寫條件式 CHECK」。
- **`expects_rejection` 掛在情境上,所以一個情境不能同時有「成功的前置訂單」與「被拒的
  請求」。** S8(既有訂單 → 改它 → 拒絕)那種混合情境在 D 底下表達不了。S8/S9/S12 屬於
  「動詞不夠」那一類、本次不做;**做那一類的時候會撞到這個限制,屆時要重審這條 ADR。**
- **本次範圍只含「fixture 違法」那 5 條**(S3–S7),不含「動詞不夠」那 3 條(S8/S9/S12)。
  兩類的修法完全不同:前者是放寬/搬移約束,後者是在 store 裡長出一套動作模型。
  混在一起做,會不知道是哪一半讓驗收過的。
- **S3 在這 5 條裡是特例**:它要的不是放寬約束,是**多一個欄位**(請求裡夾帶的總金額)
  —— 由 ADR 0004 的 wire shape 宣告點一併解決。
