# 19 — 第一幕的收尾指示把 shop 的 wire shape 寫死在通用 runner 裡

**What to build:** 把 `orchestrate.py` 的 `final_message()` 裡那句舉例欄位拿掉或改成
由 template dir 提供,讓收尾指示不再對任何一個案子的形狀洩題。

## 事實(2026-08-21 跑 timesheet 第一幕當場抓到)

`tools/harness/orchestrate.py` 的 `final_message()` 逐字寫著:

> 「情境」那一節是重點:每條要有具體的前提資料(**顧客、商品、數量、金額、幣別**)、
> 單一動作、可斷言的結果

那六個詞是 `wire_contract` 表的欄位概念,也就是 **shop 這條線的 wire shape**。
它住在 `orchestrate.py` —— 一支**與案子無關**的 runner,而 `interviewer/prompt.txt`
與 `stakeholder/spec/SPEC.md` 這些**該隨案子換**的東西全都在 template dir 裡。

後果分兩種,兩種都真:

1. **對非 shop 的案子是洩題。** 計費工時單沒有「商品」,而收尾指示叫訪談者照那個形狀
   寫情境 —— 落檔率還沒開始量,情境的形狀就先被受測品自己帶過去了。
2. **對 shop 是隱形的。** 因為剛好對,所以三跑下來沒有人看見它在那裡。

⚠️ 這跟票 08 / 票 15 是**同一族**:規則寫在一個不該擁有它的地方,而它剛好有效,
所以沒有人發現它是錯的位置。差別是那兩張講「誠實落不了檔」,這張講「洩題落得太進去」。

## 做法有兩條,先裁決再動

| | 做法 | 代價 |
|---|---|---|
| A | 那句舉例整段刪掉,只留「具體的前提資料」 | 訪談者可能不寫具體值 —— 而那句舉例本來就是為了治這個 |
| B | 舉例改由 template dir 的 `interviewer/final-hint.txt` 提供,`orchestrate.py` 讀不到就不加 | 多一份受測輸入,`stage_inputs()` 的必要清單要跟著改 |

**傾向 B**:「wire shape 歸規格擁有」是 ADR 0004 已經裁決過的事,這裡是同一條原則
沒有套用到 runner 自己身上。

## 影響到的既有素材

- `examples/timesheet/harness/runs/2026-08-21-act1/` —— **帶著這個洩題跑完的**。
  它的 `SPEC-draft.md` 情境形狀不得當成「訪談者自己判斷出來的」。
- shop 的三跑不受影響(形狀剛好對),但**它們也證明不了訪談者會自己選對形狀**。

**Blocked by:** None

**Status:** **needs-triage** —— 2026-08-21 timesheet 第一幕跑到一半當場抓到,證據見
`examples/timesheet/harness/runs/2026-08-21-act1/`(commit `216da73`)。**先裁決 A / B 再動**;
動之前要先決定 timesheet 那一跑是修完重跑、還是留著當這個洩題的實證。

- [ ] A / B 裁決有記錄
- [ ] `final_message()` 不再含任何案子專屬的欄位概念
- [ ] timesheet 第一幕的處置有裁決(重跑 or 留作實證)
