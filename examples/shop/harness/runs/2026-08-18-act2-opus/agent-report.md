驗證通過:

```
$ python3 tools/harness/spec_store.py import acceptance.yaml /tmp/spec.db
ok: acceptance.yaml → /tmp/spec.db
```

## 產出內容

**`acceptance_scenarios`** —— 就是 SPEC.md「情境(Given-When-Then)」列的那 5 條,不多不少:

| id | 情境 | assertions | ref |
|---|---|---|---|
| S1 | 單一明細下單 | `status_is` 201、`order_id_not_blank` | L44-45 |
| S2 | 已成立訂單出現在列表 | `list_row_exists`、`list_field_equals_text` statusLabel=已成立 | L46-47 |
| S3 | 列表顯示顧客姓名 | 兩筆訂單各一條 `list_field_equals_text` customerName | L48-49 |
| S4 | 多明細總額 | `list_field_equals_number` totalCents=5100 | L50-51 |
| S5 | placedAt 格式 | `list_field_is_iso_date` placedAt | L52-53 |

S4 的 fixture 刻意湊成 2×1500 + 1×2100 = 5100,對齊 SPEC.md L34 response 範例裡的 `totalCents`。S3 送兩筆(不同顧客),照 schema.sql:139-140 的註解——一筆證明不了 `customerName` 是 join 出來的而非寫死的。

## 兩件要講清楚的事

**1. 我加了一個你沒要求的頂層 key。** 你說「頂層一個 key `acceptance_scenarios`」,但 importer 的第一條錯誤是 `architecture_rules 必須是非空的 list`——不填就永遠印不出 ok。既然「改到它印 ok 為止」是完成的定義,我以 importer 為準,補了 `architecture_rules`(A1–A6),來源是 SPEC.md「領域規則(Aggregate 與契約)」L55-70——該節自己寫明「與上面的情境同等效力」。六條全部 `enforcement: none` + `ladder_note`(說明為何還沒機械化、搬得上去的話搬去哪),因為它們都是物件內部行為(setter、防禦性複本、例外),三個 archunit kind 表達不了。`enforced_by` 一概沒寫——那欄只由生成器回填。provenance 一律 `推導自` + SPEC.md 行號,沒有用 `模板既定`。

**2. S3 的姓名是推的。** `C-001` → "Alice" 由 SPEC.md 的 request 範例(L14)配 response 範例(L31)推得;`C-002` → "Bob" 是我照 schema.sql 註解裡點名的「Alice 與 Bob」補的。如果實際 seed 的 `customers` 表對應不同,S3 會在生成測試那一步才炸——那是下游資料,這一幕驗不到。