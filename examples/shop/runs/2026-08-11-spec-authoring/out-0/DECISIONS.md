# 規格決定記錄(逐字稿沒有依據的部分)

> 逐字稿只給了業務事實;下列每一條都是規格作者的裁定。實作 agent 照做即可;若營運端未來翻案,改這裡並同步三份規格。

| # | 決定 | 理由 |
|---|---|---|
| D-01 | 對外介面是 REST JSON API(`POST /api/orders`、`GET /api/orders`),不做 UI | 逐字稿只講「下單、看列表」沒講介面形式;驗收方式是自動化測試,API 最可測。列表「顯示中文『已成立』」以 response 的 `statusLabel` 欄位滿足 |
| D-02 | 「客人下單」不做認證,`customerId` 由 request 直接帶 | 會員/登入明確 out of scope,主管只要求顧客資料讀得到 |
| D-03 | 明細品項 = 自由文字 `productName` + `quantity` + `unitPrice`,不建商品主檔 | 逐字稿完全沒提商品目錄;總額公式只需要數量×單價。發明 Product aggregate 是無依據的範圍擴張 |
| D-04 | 幣別是**訂單層級**欄位(不在明細上),格式只驗 `^[A-Z]{3}$` 不驗 ISO 4217 清單 | 「一張訂單不混幣別」直接由結構保證,不需要執行期檢查混幣;主管沒給幣別清單,驗清單會猜錯範圍 |
| D-05 | 顧客姓名**讀取時**從 CRM 表解析,不 snapshot 進訂單 | 「名單 CRM 維護、你們讀得到就好」的直讀:CRM 是姓名的唯一 source of truth,改名後列表自動反映 |
| D-06 | domain 存 `OrderStatus.CREATED`;中文「已成立」是 adapter/web 的顯示映射,response 同時給 `status`(機器用)與 `statusLabel`(顯示用) | 主管的要求是「給我**看**中文」——顯示關注點;domain 塞中文字串會把 presentation 綁進核心 |
| D-07 | 訂單 id = 系統產生的 UUID 字串 | 逐字稿未提;UUID 不需要 DB 序號,測試只斷言非空 |
| D-08 | request 夾帶規格外欄位(含 `totalAmount`)一律忽略,不報錯 | 主管只說總額系統算;寬容讀取 + 伺服器計算已足夠守住「client 給的 total 不算數」 |
| D-09 | 列表排序 `createdAt` 新到舊(tie-break `orderId` 字典序遞增);不分頁 | 逐字稿沉默;「看所有訂單」最自然是最新在前,且測試需要確定性順序。量級未提,不預做分頁 |
| D-10 | `createdAt` 用 local date-time(`yyyy-MM-dd'T'HH:mm:ss`)、無 timezone;時間經 `ClockPort` 注入 | 主管只要「哪天下的」;單一營運地域下 local time 足夠。Clock port 是讓驗收測試可固定時間的必要設計 |
| D-11 | 所有建立失敗回 **HTTP 400**,error body `{error, message}`,錯誤碼只有 `CUSTOMER_NOT_FOUND` 與 `VALIDATION_ERROR` 兩個 | 逐字稿沉默;單一 status code + 粗粒度錯誤碼最小夠用,細分 422/409 對這個範圍沒有回報 |
| D-12 | `unitPrice ≥ 0`(允許 0,如贈品)、scale ≤ 2;`quantity` 為整數 ≥ 1;總額 normalize 到 scale 2 | 逐字稿只給公式沒給值域。整數數量 + scale≤2 單價 ⇒ 總額天然 scale ≤ 2,**不存在捨入問題**,規格刻意不開捨入規則的門 |
| D-13 | CRM 那張表在本系統以 H2 內的 `CRM_CUSTOMER` 表模擬,`data.sql` 灌 3 筆 seed(C001 王小明 / C002 陳大文 / C003 林美玲),存取走唯讀 port `CustomerReader` | 真實 CRM 的介接方式(DB link?API?)逐字稿沒講;demo/驗收環境用同庫唯讀表是最小模擬,port 隔離讓未來換真 CRM 只動 adapter |
| D-14 | 不預留取消/修改的任何結構(無狀態機、無多餘 enum 值、無 update endpoint) | 主管明說「先不用,以後再說」;為未定需求預留結構是猜測,猜錯成本高於將來加欄位 |

## 建議回頭跟主管確認的點(不阻塞實作)

1. D-05:顧客在 CRM 改名後,**歷史訂單**列表也會顯示新名字——這是否符合期待?(若要保留下單當下的名字,改為 snapshot,動 D-05 一條即可。)
2. D-10:是否有跨時區營運的計畫?有的話 `createdAt` 應改存 UTC instant。
3. D-04:幣別是否需要限定清單(例如只收 TWD/USD/JPY)?
