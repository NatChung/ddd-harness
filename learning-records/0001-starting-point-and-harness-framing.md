# 起點:DDD 零基礎,但目標是 agent harness 而非傳統軟體架構

Nat 自述對 DDD「只聽過名字」——講不出 Bounded Context 或 Aggregate 是什麼意思,所以所有術語
都要從零建立,不能預設任何先備知識。

關鍵的是他的 mission 不是一般人學 DDD 的理由(拆微服務、重構遺留系統、跟領域專家對話),而是
**把 DDD + BDD 當成 AI Agent development harness 的骨架**,目的是讓 agent 產出不隨換模型而漂移。

## Implications

- 教學順序不照傳統 DDD 教材(戰略層→戰術層→實作)。改照「哪個概念擋掉哪一種 agent 漂移」排:
  Ubiquitous Language(語言漂移)→ Bounded Context(範圍漂移)→ BDD 驗收(判定漂移)。
- **Aggregate 及其他 tactical patterns 延後**,不在前幾堂出現。它們對 harness 的價值要等
  前三個概念站穩才講得清楚。
- DDD 概念對應到 agent 機制(例如 Bounded Context ↔ agent 的 context 範圍)這件事,
  目前找不到第一手來源支持,是本教學自建的推論。**每次用到都要標註是推論**,
  不能講得像業界共識。這點已記在 RESOURCES.md 的 Gaps。
- 貫穿案例未定。現階段用中性小型電商例子,不碰 KC 內部系統。
