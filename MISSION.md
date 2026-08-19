# Mission: 用 DDD + BDD 建立 AI Agent 的 Development Harness

> **這份是個人的專案定位文件,原樣發布、沒有為了公開而改寫。** 它用第三人稱寫,
> 因為當初是寫給自己看的。「Nat」是作者 Nat Chung;「KC」是他任職公司的簡稱。
> 想先看這個 repo 有什麼,請讀 [README.md](./README.md);這份講的是**為什麼做**。

## Why

Nat 要建立一套 AI Agent 的開發 workflow(harness),讓 agent 產出的東西不隨著換模型而漂移。

DDD 處理的核心問題是「人跟人之間語言含糊,做出來的軟體就跟著含糊」——LLM agent 有一模一樣的
失效模式,只是它填補含糊的方式是「照訓練分佈猜一個看起來合理的」。所以 DDD 的語言與邊界,
加上 BDD 的可執行驗收,就是這個 harness 的骨架。

**能力目標對標**:陳建村(Teddy)的「馴服 AI 寫出可維護的系統:模式語言驅動開發工作坊」課綱。
Nat **不打算去上這門課**,但那份課綱精準描述了他想自己做到的事,所以拿它當本教學的驗收清單。
課綱的能力項:

1. Top-down 設計、把 context 的限制用盡、**多層次 pattern language** 的運用
2. 用 pattern language 指揮 AI 完成真實任務
3. 從架構知識設計出 pattern language;做出 sub-agent prompt template;
   組出自動化 workflow pipeline;**從 AI 犯的錯反過來演化出新 pattern**
4. 品質保證:BDD、Design by Contract、測試、code review

## Success looks like

- 能為一個 feature 寫出三件事:**Ubiquitous Language 詞彙表**、**Bounded Context 邊界**、
  **Given-When-Then 驗收情境**——並說明每一項各自擋掉哪一種 agent 漂移。
- 拿同一份規格餵給兩個不同的 model,兩邊的實作都能被**同一套驗收**明確判定通過或不通過。
  (目標不是讓模型輸出一樣,是讓「對不對」這件事不需要人來主觀判斷。)
- 能把 DDD 的戰術 pattern + 架構層的 pattern 組成一套**分層的 pattern language**,
  作為指揮 agent 的詞彙——而不是每次重寫一長串 prompt。
- 手上有一套機制:**agent 犯了錯 → 錯誤被轉成 pattern 或驗收條目 → 同類錯誤不再發生**。
  (這是課綱裡「living patterns / 從錯誤演化 pattern」那一項,也是 harness 真正會複利的地方。)
- 看得懂別人在講 spec-driven development / agent harness 時,哪些是 DDD 與 pattern language
  的既有概念換皮,哪些是真的新東西。
- 上述都落成 repo 裡可重複使用的檔案結構,不是一次性的 prompt。

## Constraints

- DDD 是**零基礎**(只聽過名字),術語一律從零建立。
- 但工程底子紮實:**Java、物件導向、design patterns、xUnit 都熟**。
  所以 DDD 可以直接架在他已有的知識上教(例:Aggregate 對比他熟的物件封裝與 invariant),
  不必從程式設計基礎鋪起,節奏可以快。
- 教材用**繁體中文**,DDD/BDD 術語保留英文原文(Bounded Context、Aggregate、Given/When/Then)。
- 術語的中文用法對齊 Teddy 體系(例:寫「簡潔架構」而非「整潔架構」),
  範例語言可直接用 Java —— 這樣他讀 Teddy 的部落格與 ezSpec 系列文時無縫接軌。
- 每堂課要短、能很快做完。

## In scope(因對標課綱而納入)

- **Clean Architecture(簡潔架構)分層** 與 **CQRS** ——不是為了考試,是因為 pattern language
  的上層就長在架構層,少了它就只剩領域層的詞彙,指揮不動 agent 做整個 feature。
- **Event Storming** —— 產出 Ubiquitous Language 與邊界的實際方法。
- **Design by Contract** —— 課綱把它跟 BDD 並列為品質保證手段。
- **ezSpec 的 BDD 模型**(Feature / Story / Scenario / Steps),而非 Cucumber 的 feature 檔那套。

## Out of scope

- DDD 戰術層的百科式教學(Repository、Factory、Specification pattern 等)先不碰,
  等 harness 骨架站穩、確定哪個真的用得到再回頭。
- Event Sourcing。CQRS 要,ES 不要——它常跟 CQRS 綁在一起講,但不是這個 mission 需要的。
- 微服務拆分策略。
- 傳統企業軟體架構顧問那一套。這裡的「domain expert」與「developer」很多時候是同一個人,
  對話對象是 agent。

---

**目前未定**:貫穿整個教學的案例還沒選定。現階段用中性的小型電商例子(訂單/庫存),
不使用 KC 內部真實系統資料。見 [NOTES.md](./NOTES.md)。
