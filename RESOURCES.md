# DDD + AI Agent Harness Resources

蒐集原則:優先第一手來源(原作者、原始工具庫、同儕審查論文)。行銷包裝成教學的一律不收。

## Knowledge — DDD 本體

- [Bliki: Bounded Context — Martin Fowler](https://martinfowler.com/bliki/BoundedContext.html)
  DDD 最核心的分割概念,Fowler 的短文版。關鍵句:邊界常常長在**語言變化的地方**——
  「you need a different model when the language changes」。
  Use for:判斷一個 agent 的作業範圍該切在哪裡。**已讀過,可直接引用。**

- [Bliki: Ubiquitous Language — Martin Fowler](https://martinfowler.com/bliki/UbiquitousLanguage.html)
  定義:「the practice of building up a common, rigorous language between developers and users」。
  關鍵句:「software doesn't cope well with ambiguity」。
  Use for:任何跟詞彙、命名、規格含糊有關的問題。**已讀過,可直接引用。**

- [Effective Aggregate Design — Vaughn Vernon(三篇免費 PDF)](https://www.dddcommunity.org/library/vernon_2011/)
  Aggregate 設計最常被引用的文獻。
  [Part I](https://www.dddcommunity.org/wp-content/uploads/files/pdf_articles/Vernon_2011_1.pdf) ·
  [Part II](https://www.dddcommunity.org/wp-content/uploads/files/pdf_articles/Vernon_2011_2.pdf) ·
  [Part III](https://www.dddcommunity.org/wp-content/uploads/files/pdf_articles/Vernon_2011_3.pdf)
  **連結已驗證存在且免費**,但 ⚠️ **PDF 內文尚未讀過**——第 4 課裡「一次交易只改一個
  Aggregate」等規矩是通行說法的轉述,要正式引用前得先讀原文。Use for:第 4 課的深化。

- [書:Domain-Driven Design — Eric Evans(2003,藍皮書)](https://www.domainlanguage.com/ddd/)
  原典。厚、難、大部分內容超出本 mission 範圍。**不建議從這本入門**,當作查證用。

- [書:領域驅動設計精粹(Domain-Driven Design Distilled)— Vaughn Vernon](https://www.tenlong.com.tw/products/9787121348525)
  中文版,約 150 頁,涵蓋 Bounded Context、Ubiquitous Language、Subdomain、Context Mapping。
  Use for:想在單堂課之外自己補戰略層時的中文入門書。
  ⚠️ 尚未親自查核內容品質,先列為候選。

- [關於 Domain-Driven Design 以及他的魅力 — iT 邦幫忙](https://ithelp.ithome.com.tw/articles/10216645)
  台灣社群的繁中入門文章。Use for:術語的中文對照。
  ⚠️ 社群文章,非第一手,引用前需交叉查核。

## Knowledge — 陳建村(Teddy)體系 ★ 最高優先

> 2026-08-09 確認:Nat **不打算報名這些課**,但 Teddy 的課綱精準描述了他想自己做到的能力,
> 所以拿課綱當驗收清單、拿 Teddy 的免費著作當主力教材。
> **這一節的來源優先於其他所有來源**——術語與寫法都以 Teddy 的用法為準
> (他寫「簡潔架構」而非「整潔架構」),這樣讀他的部落格與 ezSpec 系列文時無縫接軌。
> 課程頁只當**課綱參考**看,不要再提報名、費用、日期。

- [課綱:馴服 AI 寫出可維護的系統 — 模式語言驅動開發工作坊](https://teddysoft.tw/courses/ai-coding-pl/)
  **本教學的能力目標對標對象。** 內容:top-down 設計、把 context 限制用盡、
  **多層次 pattern language**、sub-agent prompt template、自動化 workflow pipeline、
  **從 AI 犯的錯演化出新 pattern**、品質保證(BDD、Design by Contract、測試、code review)。
  用 Java + Claude Code。它假設讀者已有 Clean Architecture / DDD / CQRS 基礎
  ——這就是為什麼那三項在本教學裡是 in scope。

- [課綱:領域驅動設計與簡潔架構入門實作班](https://teddysoft.tw/courses/clean-architecture/)
  上面那份課綱假設的基礎。用 Event Storming 建領域模型與統一語言,再用 Clean Architecture
  + TDD 實作看板系統(ezKanban)。Use for:排本教學前半段的內容順序。

- [部落格:搞笑談軟工 — DDD 標籤](http://teddy-chen-tw.blogspot.com/search/label/DDD)
  Teddy 的部落格,2007 年寫到現在。**免費,繁中,跟課程同一套術語。**
  Use for:自學路線的主力來源。

- [使用 ezSpec 落實行為驅動開發與實例化需求(系列文,共 10 篇)](https://teddy-chen-tw.blogspot.com/2023/03/ezspec1.html)
  ezSpec 是 Teddy 2021 年做 ezKanban 時開發的 Java internal DSL,
  拿掉 Cucumber/JBehave 那套 feature 檔 + Step Definition + 正規表示式的麻煩,
  **把 Given-When-Then 內容直接放進 lambda**;未實作的步驟用 `pending()` 標。
  領域模型:Feature / Story / Scenario / Scenario Outline / Steps / Background / Concurrent Group。
  自訂報表走 Visitor pattern。
  **已用於第 3 課(領域模型部分已查證)。**
  ⚠️ **注意:文章裡的 Java 程式碼全是截圖,抓不到文字。** 需要實際 API 寫法時要人工看圖,
  不要憑記憶編。各篇網址:
  [2 Feature/Story](https://teddy-chen-tw.blogspot.com/2023/03/ezspec2featurestory.html) ·
  [3](https://teddy-chen-tw.blogspot.com/2023/03/ezspec3scenario.html) ·
  [4 Scenario](https://teddy-chen-tw.blogspot.com/2023/03/ezspec4scenario.html) ·
  [5](https://teddy-chen-tw.blogspot.com/2023/03/ezspec5scenario-outline.html) ·
  [6 Scenario Outline](https://teddy-chen-tw.blogspot.com/2023/03/ezspec6scenario-outline.html) ·
  [7 Background](https://teddy-chen-tw.blogspot.com/2023/03/ezspec7background.html) ·
  [8](https://teddy-chen-tw.blogspot.com/2023/03/ezspec8.html) ·
  [9](https://teddy-chen-tw.blogspot.com/2023/03/ezspec9.html) ·
  [10 自訂報表](https://teddy-chen-tw.blogspot.com/2023/03/ezspec10.html)

- [BDD(2):大家來吃小黃瓜之 Cucumber 運作原理](https://teddy-chen-tw.blogspot.com/2013/07/bdd2cucumber.html)
  同作者 2013 年的文章,講 feature 檔 + Step Definition 那套怎麼運作。
  Use for:理解 ezSpec 拿掉了什麼。

- [課綱:實例化規格與行為驅動開發實作班](https://teddysoft.tw/courses/sbe-bdd/)
  Teddy 的 SBE/BDD 課綱。Use for:排第 3 課之後的 BDD 深化內容。⚠️ 尚未查核內容。

- [再談 Clean Architecture 三原則 — 搞笑談軟工(2020-08)](https://teddy-chen-tw.blogspot.com/2020/08/clean-architecture.html)
  ★ **第 5 課的主結構來源。** 把 Clean Architecture 收成三條原則,已核對的原句:
  **分層原則**「Clean Architecture 有四層:Entities、Use Cases、Interface Adapters、
  Frameworks & Drivers」;**相依性原則**「原始碼的依賴方向必須由外往內、由低層往高層」;
  **跨層原則**「當 Entities 層的物件跨越離開 Use Case 層往外傳遞時,不要直接把 Entities 層的
  物件傳出 Use Case 層,而是要在 Use Cases 層定義往外傳遞的介面與資料結構」。
  同系列專文:[相依性原則](https://teddy-chen-tw.blogspot.com/2018/07/clean-architecture5.html) ·
  [跨層原則](https://teddy-chen-tw.blogspot.com/2018/07/clean-architecture6.html)。
  ⚠️ **只核對了上面這三句,全文未逐字讀完。**

- [The Clean Architecture — Robert C. Martin(2012)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
  四層與 Dependency Rule 的原始出處,免費、短。已核對的原句:
  「Source code dependencies can only point inwards. Nothing in an inner circle can know
  anything at all about something in an outer circle.」以及跨界時傳的應該是
  「simple data structures」、「We don't want to cheat and pass Entities or Database rows」。
  另外已核對兩句(第 5 課補充段用):**層數不是規定**——「the circles are schematic. You may
  find that you need more than just these four. There's no rule that says you must always have
  just these four. However, *The Dependency Rule* always applies.」;**內外的判準**——
  「As you move inwards the level of abstraction increases. The outermost circle is low level
  concrete detail. As you move inwards the software grows more abstract, and encapsulates
  higher level policies.」
  **已用於第 5 課。**⚠️ 同樣只核對引用句,全文未逐字讀完。

- **Evans 的 DDD 四層(User Interface / Application / Domain / Infrastructure)**:
  第 5 課的對應表用到,但 ⚠️ **來源是社群整理而非藍皮書原文**——
  [ajlopez](https://ajlopez.wordpress.com/2008/09/12/layered-architecture-in-domain-driven-design/)、
  [SSENSE Tech](https://medium.com/ssense-tech/domain-driven-design-everything-you-always-wanted-to-know-about-it-but-were-afraid-to-ask-a85e7b74497a)。
  多個來源說法一致,但要正式引用得回去查書。同樣未查證的還有
  「Evans 把 Repository 放 Domain 層、Clean Architecture 這派放 Use Cases 層」這個差異。

- [Clean Architecture 之 CQRS Pattern — 搞笑談軟工](https://teddy-chen-tw.blogspot.com/2020/09/clean-architecturecqrs-pattern.html)
  ★ **第 6 課的主來源,已用於第 6 課。** 它處理的問題是「為什麼 CQRS 架構中特意允許跨層參考」
  ——正好接續第 5 課的跨層原則。Query 側的做法:`GetUserUseCase` 用 `UserQueryRepository`
  查 DB、直接回 `UserDto` 給前端,不經領域物件;代價是重複,他認為值得。 已核對的原句:「領域驅動設計(Domain-Driven Design;DDD)只需要應用在
  那些會改變系統狀態的 Command。換句話說,只需要在 Command 套用 DDD 與 Clean Architecture」;
  Query 側則「不需要套用 DDD,甚至根本也不要設計領域物件,直接讀取資料庫然後產生前端需要的
  View Model 即可」。⚠️ 只核對這兩句,全文未逐字讀完。

- **術語確認(2026-08-10)**:[簡潔架構入門實作班課綱](https://teddysoft.tw/courses/clean-architecture/)
  頁面同時出現兩種譯法——課程內文用「**簡潔架構**」(「在實作階段,套用簡潔架構,採用測試驅動
  開發方法」),提到書名時才寫「《Clean Architecture》(中文版《整潔的軟體設計與架構》)」。
  → MISSION.md 的「寫簡潔架構、不寫整潔架構」這條慣例**已查證屬實**。

- [影片:[2020 DDDTW 年會] DDD + Clean Architecture 從需求到實作 — 陳建村](https://www.youtube.com/watch?v=5THBVeKtJr8)
  **免費、繁中、同一位講師,講的正是 DDD 接到 Clean Architecture 的完整路徑。**
  Use for:想一次看完全貌時。⚠️ 尚未看過,需查核長度與涵蓋範圍。

- [領域驅動設計與整潔架構基礎課程筆記 — Miles' Blog](https://mileschou.me/blog/ddd-and-ca-started-day-2/)
  他人上完該課的筆記。Use for:對照本教學有沒有漏掉重要環節。⚠️ 二手,尚未查核。

- [CQRS — Martin Fowler](https://martinfowler.com/bliki/CQRS.html)
  **已用於第 6 課。**已核對的原句:定義「you can use a different model to update information
  than the model you use to read information」;警告「You should be very cautious about using
  CQRS」「for most systems CQRS adds risky complexity」;以及「CQRS fits well with event-based
  programming models」(所以 Event Sourcing 常跟它一起出現,但不是必需)。
  出處歸屬也已核對:「It's a pattern that I first heard described by Greg Young」
  ——要提原創者時引這句,不要憑印象寫。
  ⚠️ 只核對這幾句,全文未逐字讀完。

## Knowledge — Event Storming

- [Introducing Event Storming — Alberto Brandolini(2013)](https://ziobrando.blogspot.com/2013/11/introducing-event-storming.html)
  ★ **第 7 課的主來源。**已核對的原句:Domain Event 的定義「A **Domain Event** is something
  meaningful happened in the domain. It can be easily translated into *software*, but the real
  value here is that it could be quickly grasped from non-technical people.」;
  討論變熱時要「define a clear acceptance test」;
  以及「Embracing incompleteness will make the workshop less boring and more fruitful.」
  工作坊三階段:Big Picture / Process Modeling / Design Level。
  ⚠️ 只核對這幾句,全文未逐字讀完。

- [eventstorming.com](https://www.eventstorming.com/)
  官方站。定義原句:「a flexible workshop format for collaborative exploration of complex
  business domains」。有 Improve / Envision / Explore / Design 幾種型態。
  ⚠️ 站上**沒有**解釋「為什麼用過去式事件當起點」——第 7 課那個理由是本教學自己補的論證。

- [ddd-crew / eventstorming-glossary-cheat-sheet](https://github.com/ddd-crew/eventstorming-glossary-cheat-sheet)
  ★ **標記法的來源(顏色 + 定義),第 7 課的表格出自這裡。**免費,可直接印出來當工作坊用。
  Domain Event(橘)、Command/Action(藍)、Actor(小黃)、Policy(紫)、Query Model(綠)、
  Hotspot(鮮粉紅)、System(寬粉紅)。
  ⚠️ 注意:它把 **Aggregate 標為 legacy 用法**,改用大張黃色的 **Constraint**
  ——Brandolini 原文與多數繁中材料仍用 Aggregate,第 4 課與第 7 課都照舊,只加註說明。

- 陳建村的 Event Storming 系列(繁中,術語:**事件風暴 / 領域事件**,
  Command / Aggregate / Policy 保留英文,與本教學一致):
  [領域事件幫你切割使用案例](http://teddy-chen-tw.blogspot.com/2020/02/blog-post.html)
  (已核對原句:「使用 Event Storming,依據時間軸來思考領域事件,再寫出相對應的 Command,
  系統的行為就會慢慢浮現出來。」——他用這方法發現一個 use case 該拆成兩個)、
  [Event Storming 與 User Story](https://teddy-chen-tw.blogspot.com/2020/12/12event-storminguser-story.html)、
  [幫 Event Storming 加上使用者介面](https://teddy-chen-tw.blogspot.com/2020/12/13event-storming.html)。

> ⚠️ **沒有實際參與或帶過 Event Storming 工作坊。**第 7 課只能講方法宣稱怎麼運作,
> 「現場實際會發生什麼」答不了。若之後 Nat 真的跑一場,回來補一則 learning record。

## Knowledge — Agent Harness / Spec-Driven Development

- [Think Before You Prompt: what SDD is and isn't, plus a taxonomy of agent harnesses](https://codagent.beehiiv.com/p/think-before-you-prompt)
  把 harness 定義成「the rest of the car」——模型是引擎,harness 是方向盤、煞車、車道線。
  區分 coding agent(產品層)與 engineering layer(開發者自建層,分成 information architecture /
  coordination & control / infrastructure 三類)。並明確反駁「SDD = waterfall 換皮」:
  差別在 spec 與執行之間的回饋迴圈以分鐘計,且 spec 會隨失敗共同演化。
  Use for:harness 的整體架構分類。**已讀過,可直接引用。**

- [GitHub Spec Kit](https://github.com/github/spec-kit) / [文件](https://github.github.com/spec-kit/) /
  ★ [spec-driven.md(方法論本體)](https://raw.githubusercontent.com/github/spec-kit/main/spec-driven.md)
  開源工具包,把 SDD 流程固化成 constitution → specify → plan → tasks → implement。
  支援 30+ 種 coding agent。
  ⚠️ **原本寫過一課專門拆它,2026-08-11 已刪除**(標本挑錯——Nat 不用這個工具;
  見 NOTES 課表)。下面這些引用句是那次查證的成果,**保留下來免得重查**,
  但目前沒有任何一課在用。
  已核對的原句:「Specifications don't serve code—code serves specifications」;
  「We're moving from *code is the source of truth* to *intent is the source of truth*」;
  模板命令 LLM「Mark all ambiguities: Use [NEEDS CLARIFICATION: specific question]」、
  「If the prompt doesn't specify something, mark it」而非 making plausible assumptions;
  spec 要「Focus on WHAT users need and WHY」、避免「HOW to implement (no tech stack,
  APIs, code structure)」;憲法(`memory/constitution.md`)九條被形容成
  「compile-time checks for architectural principles」(Article I Library-First、
  II CLI Interface、III Test-First、IV–VI 各團隊自填、VII Simplicity、VIII Anti-Abstraction、
  IX Integration-First Testing)。產物路徑:`specs/###-feature/{spec,plan,tasks,research,
  data-model}.md` + `contracts/`。
  ⚠️ 四份來源都只核對引用句、未逐字讀完,而且**沒有實際跑過這個工具**——
  第 7 課只講它宣稱怎麼運作,不評論實際體驗。

- [Spec-driven development with AI — GitHub Blog](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/)
  Spec Kit 的官方說明。Use for:理解 constitution(專案憲法)這一層在做什麼。

- [Spec-Driven Development with Coding Agents — DeepLearning.AI](https://www.deeplearning.ai/courses/spec-driven-development-with-coding-agents)
  課程。Use for:想要有人帶著走一遍完整流程時。⚠️ 尚未查核課程內容。

- ★ [A Field Guide to Claude Fable 5: Finding Your Unknowns — Thariq Shihipar(Anthropic, 2026-07-06)](https://claude.com/blog/a-field-guide-to-claude-fable-finding-your-unknowns)
  把「已知的已知 / 已知的未知 / 未知的已知 / 未知的未知」四象限套到與 AI 協作:
  **只有第一象限安全**,其餘三種 AI 只能猜,而且猜得合理,你要看到成品才發現怪怪的。
  主張瓶頸已從模型能力移到「你能不能把自己不知道的東西講清楚」。按時機給 8 招
  (動工前 5:Blind Spot Pass / Brainstorms and Prototypes / Interviews / References /
  Implementation Plans;動工中 1:Implementation Notes;動工後 2:Pitches / Quizzes)。
  已核對的原句:訪談那招是「一次問我一題,問任何模糊的地方,**優先問那些我的答案會改變
  架構的問題**」;收束句是「每一次說帖、每一次腦力激盪、每一次訪談、每一個雛形、每一份
  參考範例,都是趁事情還便宜的時候先發現你不知道的東西」。
  Use for:背景讀物與日後引用備料。⚠️ **2026-08-19 起第 0 課不再引用它** ——
  中場那段拿掉了(那格的論點已由「三份 prompt 打開來數」的字元數直接證明,不需要外部權威)。
  **原文已讀過,要用可直接引用。**

- [Matt Pocock — Software Fundamentals Matter More / Workflow for AI Coding(談話)](https://www.youtube.com/watch?v=v4F1gFy-hqg)
  第 0 課第 2 級引的那句「只改 spec、不看 code、反覆重跑,越跑越爛,本質是 vibe coding
  改名」出自這裡,理由掛在《Pragmatic Programmer》的**軟體熵**。同一批談話也是
  「借 DDD 的 ubiquitous language 跟 AI 建立共用術語表」的出處。
  **逐字稿讀過,這兩點可以說「Matt 本人說」。**

- ⚠️ [Gary Chen — 拆解 Matt Pocock 的 skill repo(中文,2026-07-22)](https://www.youtube.com/watch?v=aR97E7aKEgg)
  第 0 課第 4 級的素材大半來自這裡:五行 skill 的內容拆解、對「接管式大框架」的批評
  (一步定歪、錯誤沿線傳染)、`writing-great-skills` 三原則(修剪 / 指引詞 / 完成標準)、
  code review 用 12 種具名爛味道、刪除測試揪淺模組,以及**小 skill 與「整條寫死的大流程」的比較**
  (模型笨時保母級防呆管用,模型變聰明後死規矩變累贅)。
  ⚠️ **這是二手轉述** —— 講者在拆別人的 repo,不是原作者本人。現場要說「有人把他的
  repo 拆開來看」,不要講成 Matt 的原話。
  ⚠️ **「五行」已過期(2026-08-19 直接讀本機安裝的檔查證)**:內容搬進
  `skills/productivity/grilling/SKILL.md`,指令本體 **4 行、106 個英文字**(相逼問到共識+走決策樹+每題附建議答案 /
  一次一題 / **事實自己去環境查、決定才問我** / 沒共識前不准動手);
  `skills/productivity/grill-me/SKILL.md` 與 `skills/engineering/grill-with-docs/SKILL.md`
  都退成**一行 wrapper**(後者 = `/grilling` + `/domain-modeling`);
  另有 `skills/in-progress/batch-grill-me/SKILL.md` 是**每輪問完整個 frontier** 的版本。
  第 0 課引用的是這份現況,不是影片裡的五行。
  ⚠️ 影片提到的 star 數與下載數(16 萬 / 700 萬)與其他來源(約 13k stars)**互相矛盾**,
  未查證前不引用任何一個數字。
  ✅ **九步已確認**:Nat 手上有該影片的「一套定義完整的 AI 工作流」投影,九步逐一具名
  (釐清目標 / 寫規格 / 寫計畫 / 拆任務 / 設計 / 寫測試 / 實作 / 審查 / 收尾),第 0 課照這張畫。
  另有一筆第一手紀錄把同一條 pipeline 記成 7 步,是顆粒度不同,不是矛盾。

## Knowledge — Pattern Language

> 2026-08-11 補齊。**在此之前這個詞不准在教材裡定義**(原 Gaps 第一條),現已解除。

- **Christopher Alexander,《A Pattern Language: Towns, Buildings, Construction》(1977)**
  ⚠️ **不是免費的,沒有讀過原書。**第 9 課用到的兩句引言,來源狀態不同,引用時要分清楚:
  - 「Each pattern describes a problem which occurs over and over again in our environment,
    and then describes the core of the solution to that problem, in such a way that you can
    use this solution a million times over, without ever doing it the same way twice.」
    —— **多個二手來源一致,但沒看到原書頁面。**
  - 「A pattern language is a network of patterns that call upon one another.」與
    「A careful description of a perennial solution to a recurring problem within a building
    context, describing one of the configurations that brings life to a building.」
    —— 透過 [Wikipedia: Pattern language](https://en.wikipedia.org/wiki/Pattern_language)
    轉引,該處註明出自原書 **p.1216**。
  **要正式引用一律回查原書。**

- **未補**:Alexander《The Timeless Way of Building》——pattern language 的**理論卷**
  (《A Pattern Language》是它的目錄卷)。以及 **GoF 對 Alexander 的引用與轉化**:
  軟體界拿走了 pattern,大致沒有拿走 language,那個落差本身值得讀。
  第 9 課頁尾已把這兩項列為「還沒補的」。

- [用模式語言解決設計問題 — 搞笑談軟工(2016)](http://teddy-chen-tw.blogspot.com/2016/05/cc-agile-sprint-45.html)
  ★ **繁中定義的來源。**已核對:「模式語言由一群相互關聯的模式所組成」;
  目的是達到 Alexander 的「Quality Without A Name(**無名特質**)」;
  作用是「提供了溝通的共同基礎,讓一般人可以使用模式語言來解決複雜的設計問題」。

- [領域驅動設計學習筆記(2)— 搞笑談軟工](https://teddy-chen-tw.blogspot.com/2016/08/2.html)
  ★ **第 9 課「分層」那張表的靈感來源。**已核對:「這個共通語言可以是 Alexander 的
  Pattern Language,或是 DDD 所提到的 Ubiquitous Language」;他列的 pattern 層次
  「process pattern、analysis pattern、architecture pattern、design pattern、test pattern、
  implementation pattern、CI/CD pattern、HCI pattern」;
  「DDD 用 Pattern Language 的方法來打通任督二脈…可以在同一個舞台上形成開發團隊的
  Ubiquitous Language」。**這正是 MISSION 課綱裡「多層次 pattern language」的出處。**
  ⚠️ 只核對引用句,全文未逐字讀完。

- [搞笑談軟工 — Patterns 標籤](http://teddy-chen-tw.blogspot.com/search/label/Patterns)
  他從 1997 年就在寫 pattern,博士研究也是 pattern 相關。要深挖繁中材料從這裡開始。

## Knowledge — Design by Contract

- ★ [Applying "Design by Contract" — Bertrand Meyer, IEEE Computer, Oct 1992](https://se.inf.ethz.ch/~meyer/publications/computer/contract.pdf)
  **第 8 課的主來源,而且是本 workspace 目前唯一「真的讀過原文」的第一手來源**
  ——前五頁(概念部分)已用 Read 逐頁讀過,不是靠摘要。已核對的原句:
  歸屬「A precondition violation indicates a bug in the client (caller). The caller did not
  observe the conditions imposed on correct calls.」/「A postcondition violation is a bug in
  the supplier (routine). The routine failed to deliver on its promises.」;
  合約保護兩邊「It protects the client by specifying *how much* should be done. […]
  It protects the contractor by specifying *how little* is acceptable」;
  對防禦性程式設計的批評「Adding possibly redundant code "just in case" only contributes to
  the software's complexity — the single worst obstacle to software quality […] more checks,
  and so ad infinitum.」;絕對規則「Either you have the condition in the Require, or you have
  it in an If instruction in the body of the routine, but never in both.」;
  快遞合約例(Table 1)與 `put_child` 的 Eiffel require/ensure 例(Figure 2)。
  ⚠️ **後半(例外處理、rescue clause、繼承與 subcontracting)沒讀**,第 8 課也沒講。
  PDF 已下載於本 session 的 tool-results,要深挖再讀後半。

- [領域驅動設計學習筆記(14):透過合約讓領域模型與通用語言更精確 — 搞笑談軟工](https://teddy-chen-tw.blogspot.com/2021/03/14.html)
  繁中,術語:**依合約設計**、**前置條件**。已核對的重點:看板系統裡 `Card.move()` 的
  precondition 需要「目標 Stage 的卡片總數」,但 `Card` 這個 Aggregate 沒有那個資訊
  → 結論是方法該搬到 `Workflow`。結論句「透過撰寫合約讓領域模型與通用語言更加完整」。
  **這是第 8 課「契約是一種診斷工具」那一節的來源。**⚠️ 只核對引用句,全文未逐字讀完。

## Knowledge — BDD / 可執行驗收

- [Epic-Organized vs. Requirement-Aligned Gherkin: An Empirical Evaluation of LLM-Based
  Acceptance Criteria Generation(SEET 2026)](https://arxiv.org/html/2607.01980v1)
  同儕審查。比較兩種 Gherkin 組織方式對 LLM 產出驗收條件的影響。
  Use for:要主張「結構化驗收有效」時的證據來源。

- [Comprehensive Evaluation of LLMs in the Automation of BDD Acceptance Test
  Formulation](https://arxiv.org/pdf/2403.14965)
  Use for:LLM 產 Gherkin 的能力邊界與已知失效模式。

- [How to Write Effective Gherkin Acceptance Criteria — TestQuality](https://testquality.com/how-to-write-effective-gherkin-acceptance-criteria/)
  Given/When/Then 的寫法規範。Use for:寫第一份 Gherkin 時的格式參考。

## Wisdom (Communities)

- [DDD Crew(GitHub org)](https://github.com/ddd-crew)
  實務工作者維護的開源工具集(Context Mapping、Bounded Context Canvas、EventStorming glossary)。
  比論壇更有用:直接給你可以填的表格。⚠️ 尚未逐一查核,但社群聲譽高。
- [Domain-Driven Design Taiwan / iT 邦幫忙 DDD 標籤](https://ithelp.ithome.com.tw/tags/articles/DDD)
  繁中討論。Use for:術語中文化的在地慣例。

> **2026-08-10 已問過一次,Nat 沒有回應**(當下他關心的是第 4 課的觀念與往下一課)。
> 依原本的約定:問過就算數,**之後不要再提**——他想加入的話會自己說。

## Gaps

- ~~缺:pattern language 的第一手來源~~ → **2026-08-11 已補,見下面獨立一節。
  這個詞現在可以在教材裡定義了(第 9 課已定義)。**
- **缺:針對「同一份 spec 餵不同 model,產出差異有多大」的直接量測研究。**
  這正是 mission 的核心假設,但目前找到的資料都是間接支持(結構化格式提升一致性),
  沒有跨模型變異數的實測。→ 未來 session 要專門找,或者自己做一次小實驗。
- **缺:DDD 概念直接對應到 agent context 管理的第一手論述。**
  目前的對應(Bounded Context ↔ agent 作業範圍)是本教學自己建立的推論,不是引用來的。
  教材中必須標註這是推論而非既有共識。
- **已下載未讀**:`The Productivity-Reliability Paradox: Specification-Driven Governance for
  AI-Augmented Software Development`(arXiv 2605.01160)。PDF 已存於本 session 的
  `tool-results/webfetch-1786229625411-bi4sgl.pdf`,用 Read 的 `pages` 參數可讀。
  未來要引用「規格治理提升可靠度」的量化證據時先挖這篇,不要重新抓。
