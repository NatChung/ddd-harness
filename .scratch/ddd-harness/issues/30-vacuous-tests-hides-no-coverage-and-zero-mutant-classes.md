# 30 — `vacuous_tests` 只看測試:PIT 報 `Order.restore` NO_COVERAGE、`OrderStatus.java` 0 個 mutant,它一個字都不印

**What to build:** `vacuous_tests.py` 多兩段(都是佇列不是判決):每個 NO_COVERAGE 的方法列出來;
每個 0 mutant 的 class 列出來並查因(PIT 的 `targetClasses` 沒涵蓋?enum 沒 mutator?)。

**Blocked by:** None

**Status:** needs-triage —— 2026-08-25 票 13 跑 PIT 時發現(13-RESULT P2),尚未開工。

## 哪裡壞了

票 13 對 `runs/2026-08-19-act4/` 跑 PIT(71 mutant、9 條內圈測試),`vacuous_tests` 佇列 5/9。
兩個已知陽性:
- 陽性一(`Order.restore` 被 `!isStatic` 濾掉,「範圍不足」)—— PIT 資料裡 `Order.restore` 是 **NO_COVERAGE**。
  影子就在 `mutations.xml`,`vacuous_tests` 不讀那一欄。
- 陽性二(`RECEIVED -> null`)—— `OrderStatus.java` **0 個 mutant**,PIT 根本沒碰它。
  所以票 13 說的「這種 mutant 現在活得下來」其實是「這種 mutant 根本沒被生出來」,更糟。

## 形狀

- 讀 `mutations.xml` 的 `status="NO_COVERAGE"`,按 class.method 聚合,印「內圈測試碰不到的方法」佇列。
- 讀 PIT 的 class 清單對 `src/main/**` 的 class 清單,差集印「0 mutant 的 class」;對 enum 多印一句
  「enum 的 switch 回傳值 PIT 預設 mutator 不動」(**推斷,要查 PIT 文件驗**)。
- 兩段都自成一類,不進原本的「恆真 / 重複」計數;離開碼不變(佇列)。
- 考卷:`fixtures/exams/vacuous_tests/` 至少 clean / no-coverage / zero-mutant 三個 case(合成 `mutations.xml`)。

## 慣例(ADR 0007)

「內圈測試要碰到每個 public 方法」—— **不立**這條;本票只印,prose-only, unenforced。

## 完成的定義

- `30-PREDICTION.md`:對票 13 留在 scratchpad 的 `mutations.xml`(若還在;不在就重跑 PIT)→ 預期 NO_COVERAGE 含 `Order.restore`、0 mutant 含 `OrderStatus`。
- `test_vacuous_shadows.py`(新檔)。
