# Ordering(訂單)

這個 context 負責「客人下單」與「營運方檢視所有訂單」。顧客主資料屬於 CRM,不在本 context 內維護。

## Language

**Order(訂單)**:
顧客一次下單所成立的紀錄,由一條以上 OrderLine 組成,整張只用一種幣別;成立即鎖定,內容不可再變更。
_Avoid_: Purchase, Transaction

**OrderLine(明細)**:
Order 內的一條品項,記品名(自由文字)、數量、單價;每張 Order 至少一條。
_Avoid_: Item, Detail

**Customer(顧客)**:
CRM 顧客名單上的下單者,只有顧客編號與姓名兩個欄位;本 context 唯讀,不新增、不修改。
_Avoid_: 會員(Member), User, Account

**Total(總額)**:
Order 的金額,由系統計算 = Σ(明細數量 × 單價),絕不由人工輸入;幣別同該張 Order。

**Currency(幣別)**:
Order 的計價幣別;不同 Order 可以不同幣別,但一張 Order 內不混幣。

**Confirmed(已成立)**:
Order 成立後的唯一狀態;對營運方一律顯示中文「已成立」。
_Avoid_: Created, Completed, 已完成
