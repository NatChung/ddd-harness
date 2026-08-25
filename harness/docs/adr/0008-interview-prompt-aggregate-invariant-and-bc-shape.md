# ADR 0008 — 訪談 prompt §1 / §1.1 的兩格:Aggregate 以 invariant 判定;Bounded Context 要寫對外 API 與整合模式

## Status

**Proposed**(2026-08-25)—— **blocked**:`PIPELINE.md`〈現在缺的〉第 1 項「opus 跑一次幕一」
還欠著,而它量的是**現在這份** `interview-prompt.md`。先改 prompt,那一跑就在量另一支儀器。
解 blocked 的條件二選一:opus 那跑跑完;或 Nat 明說放棄那跑。落地見票 27。

## Context

`harness/interview-prompt.md` 是第一幕的受測品,也是 DDD 格子的唯一來源。
本機深讀兩個對照組後(`docs/research/2026-08-25-harness-survey.md` §9 第 6、7 條)
發現它少兩樣別人有、而且能接上機器的格子:

1. **§1 的 DDD 型態判定沒有判準。** 型態只能從七個裡選,但沒說**怎麼選**。Agentheim 的
   `agents/tactical-modeler.md` L44 一句話:「Aggregates protect invariants. If there's no
   invariant, you don't need an aggregate」;它的 BC README §Aggregates 每個 Aggregate 只寫
   一句「protects: …」。我們 §3 的「守在哪個聚合根內」是**填格**,不是從 invariant **推**出來的。
2. **§1.1 Bounded Context 只寫「切幾個、各留哪些詞、跨界用什麼關聯」。** ai-harness-template
   `methodologies/ddd-lite/templates/bounded-context.yaml` 有 `public_api`(command / query /
   event 三型)與 `integration.pattern`(shared-kernel / customer-supplier / conformist /
   anticorruption-layer / open-host / published-language);`glossary-entry.yaml` 有
   `cross_context`(same / similar / different)。**他們的模板有這些格子,但機器一格都不讀**
   (驗過:`check-context-boundary.sh` 只讀 `paths`)。我們接上就是差異。

## Decision(proposed)

- **§1**:DDD 型態欄加判準 —— 「標 `Aggregate Root` 的詞,§3 必須有至少一條 invariant 指名
  守在它裡面;反過來,§3 每條 invariant 的『守在哪個聚合根內』必須是 §1 標了 Aggregate Root
  的詞。」兩個方向都能機械對譯(`contract_triage` 加一段,或新檢查)。
- **§1.1**:每個 context 加兩格 —— 「對外 API」(逐條:command / query / event + 名字)與
  「整合模式」(六選一 + 依據)。§1 詞彙表加選填欄「跨 context 同名」(same / similar / different)。
- **落檔**:`schema.sql` 加 `bounded_context`(id、name、integration_pattern CHECK 六選一)
  與 `bc_public_api`;`glossary_term` 加 `cross_context_relation` 選填。**沒宣告就是不適用**,
  不折進通過。

## Consequences

- 動的是受測品:票 27 要先寫 `27-PREDICTION.md`,並在 `run-meta.json` 記 prompt blob。
- 不得與 2026-08-19 之前的跑比基線(與 `PIPELINE.md` 幕二那條同款警語)。
- **沒驗過的**:加了判準之後訪談者會不會把每個名詞都硬標成 Aggregate Root 來滿足對譯。
  這正是預測檔要釘的第一條。
