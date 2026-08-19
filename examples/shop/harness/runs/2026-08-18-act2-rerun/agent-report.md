完成。`acceptance.yaml` 已產出,`python3 tools/harness/spec_store.py import acceptance.yaml /tmp/spec.db` 印出 **ok**。

## 落了什麼

**12 個情境:S1–S12。** S13 不落檔 —— 它是刻意留白的阻斷級缺口(SPEC.md L126-L134、L302),不得實作。

| 類型 | 情境 |
|---|---|
| 預期成功(steps + assertions) | S1、S2、S3、S8、S9、S10、S11、S12 |
| 預期被拒(rejected_requests + rejected_assertions) | S4、S5、S6、S7 |

四條被拒情境都同時有 `status_is` 與 `list_no_row_for_customer`,且違法的值原樣送出去:S4 送空 items、S5 送數量 0、S6 送 -1、S7 送空字串的客人編號。被拒用的 `C-004/005/006/""` 沒有出現在任何成功情境(成功用的是 C-001/002/003/007/008)。

## wire_contract(本案自決的部分)

散文只把 `POST /orders` / `GET /orders` 標成自決,沒有逐欄定義,所以這些是我決定的、寫成合約讓實作照做:

- **欄位名**照 §詞彙表對譯,不另創同義詞:`customerId` / `items` / `productId` / `quantity` / `unitPriceCents` / `currency` / `totalCents` / `orderId` / `placedAt` / `status`。金額一律整數「分」(L36 固定 2 位小數、L244 禁浮點)。
- **狀態碼**:成立 201;結構上不成立(空單、數量 < 1)400;未登入 401。
- **狀態值**用原詞 `已成立`(L148、L170 禁止另創同義詞)。
- 兩個條件式必填欄都給了:`res_total_field: totalCents`(Σ 不變式靠它認人)、`res_customer_id_field: customerId`(四條被拒情境的 `list_no_row_for_customer` 靠它比對)。列表本來就要顯示「是哪個客人下的」,而訂單只保存客人編號,所以揭露的就是它。
- `req_total_field: totalCents` —— S3 要真的送一個總金額進去,才證明得了它被忽略。

## 四條代理編碼(已填 proxy_for,綠了也不等於原文成立)

schema 沒有那些動詞,我用別的東西近似,而每條都只覆蓋到一半:

- **S8**(修改被拒)—— 沒有「修改訂單」動作,且 `expects_rejection` 掛在情境上,「成功前置單 + 被拒修改」表達不了(schema.sql L255-L257)。只證明了**內容不變**,沒證明**修改請求被拒**。
- **S9**(取消被拒)—— 沒有「取消」動作。只證明了狀態仍為已成立,取消請求送不出去。
- **S10**(調價後舊單不動)—— 沒有「調整商品單價」動作(商品目錄不在範圍,L224)。只證明了訂單存的是下單當時的單價複本,**沒證明調價之後**。
- **S12**(寫到一半掛掉)—— 沒有故障注入。只證明了「完整成立」那一半,「故障後完全不存在」那一半證明不了。

另外 S11 的「不提供搜尋框/篩選器/排序」目前的斷言語彙表達不了,但它的動作(開啟列表)本身有被執行,所以不算代理編碼,沒填 proxy_for。

provenance 全部落在 schema 允許的五格內(11 條 `Qn`、S12 一條 `本案自決`),`模板既定` 為 0 筆 —— 本案沒有任何被授權為架構模板的文件。