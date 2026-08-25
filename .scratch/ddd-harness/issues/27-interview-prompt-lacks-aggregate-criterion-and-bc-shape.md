# 27 — 訪談 prompt §1 沒有 Aggregate 的判準,§1.1 沒有對外 API 與整合模式那兩格

**What to build:** 落地 ADR 0008:`interview-prompt.md` §1 / §1.1 加格與判準;`schema.sql` 加
`bounded_context` / `bc_public_api`;`contract_triage` 加「Aggregate Root ↔ invariant 雙向對譯」。

**Blocked by:** ADR 0008 的 blocked 條件 —— `PIPELINE.md`〈現在缺的〉第 1 項 opus 跑一次幕一
(對**現在這份** prompt),**或 Nat 明說放棄那跑**。⚠️ 不是「等票 21 / 22 做完」就能開。

**Status:** blocked —— 2026-08-25 Nat 拍板要做(survey §9 #6 + #7),但這張動的是受測品,
等 ADR 0008 解 blocked。

## 為什麼要等

改 `interview-prompt.md` = 換儀器。欠著的那一跑量的是舊儀器;先改再跑,就永遠不知道
舊的那支到底準不準。這跟 `examples/returns/interview-prompt.md` 凍結是同一個道理。

## 開工時照做

1. 先寫 `27-PREDICTION.md`,第一條釘 ADR 0008 Consequences 那個風險:**加了判準之後訪談者會不會
   把每個名詞都標成 Aggregate Root 來滿足對譯** —— 預測 17 詞裡標 Aggregate Root 的 ≤ 3。
2. `run-meta.json` 記新 prompt 的 blob;寫明不得與 2026-08-19 之前的跑比基線。
3. `contract_triage` 加的那段分開印,**不合併計數**(票 06-A 的教訓)。
4. `schema.sql` 的 `integration_pattern` 用 CHECK 六選一;沒宣告 → 不適用。

## 慣例(ADR 0007)

「Aggregate Root 必有 invariant、invariant 必指 Aggregate Root」由 `contract_triage` 新段守。
「整合模式六選一」由 schema CHECK 守。`cross_context` 那欄:prose-only, unenforced(對譯要人判)。
