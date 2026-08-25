#!/usr/bin/env python3
"""領域契約的分診佇列 —— 哪幾條守不住、哪幾條指不出測試。

票 06-A 買到的東西就是這支能跑:**契約進了 store 之後,
「這條契約有沒有指名測試」「哪些契約守不住」變成兩句 SELECT**,
而不是靠人去讀散文裡有沒有 ⚠️。

⚠️ **這支不生成任何可執行的東西,也不宣稱任何契約被機械檢查守著。**
   「有指名測試」與「由誰強制」是**兩件事**,分兩段印,不合併計數 ——
   合併就是把 invariant → example 的降級蓋掉,而那正是這張表要抓的東西。

⚠️ **契約 0 條 = 這項檢查不適用,不是通過**(ADR 0005 §6)。
   自成一類、印在最上面、給自己的離開碼。

離開碼:
    0  沒有待處理項目
    1  有分診項目(要人去看)
    2  用法錯誤
    3  **不適用** —— 這份 store 一條契約都沒有。不是通過。

用法:
    python3 contract_triage.py <spec.db>
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

# 分診佇列一:在自己那個物件內守不住的契約。
# 散文把「誰守」與「⚠️ 守不住」擠在同一格,擠在一起就只能靠人讀;
# 拆成三欄之後它就是一句 SELECT。
CROSSING_SQL = """
SELECT id, kind, guarded_in, disposition
FROM domain_contract
WHERE crosses_aggregate = 1
ORDER BY id
"""

# 分診佇列二:一條指名測試都指不出來的契約。
# 零列跟「還沒填」長得一樣,所以理由是必填的(第 2 階),而且這裡**逐字印** ——
# 「規格沉默,真的指不出來」與「指得出來但對面還沒落檔」是兩種零列,計數分不開。
NO_TEST_SQL = """
SELECT c.id, c.kind, c.no_named_test_reason
FROM domain_contract c
LEFT JOIN contract_named_test t ON t.contract_id = c.id
WHERE t.contract_id IS NULL
ORDER BY c.id
"""

COUNTS_SQL = """
SELECT
    (SELECT count(*) FROM domain_contract),
    (SELECT count(DISTINCT contract_id) FROM contract_named_test),
    (SELECT count(*) FROM domain_contract WHERE enforcement <> 'none'),
    (SELECT count(*) FROM domain_contract WHERE crosses_aggregate = 1)
"""

LIMITS = """
--- 這份佇列的上限(讀之前先看)---
* **「有指名測試」不等於「有機械檢查」。** 一條契約說的是「任何時候都成立」,
  而一個情境只證明了「那一筆成立」。**invariant 被降級成 example** ——
  這張表看得見那個降級,擋不住它。兩欄分開印就是為了不讓它被蓋掉。
* **`enforcement` 今天的值域只有 `none`**(沒有任何生成器讀 domain_contract),
  所以「none 佔 100%」是 CHECK 逼出來的,**不是量出來的發現**。
* **跨聚合根那一欄記的是「規格標了什麼」,不是重新判定的結果。**
  散文漏標的條目照樣進不了佇列 —— 這一欄擋不住漏標。
* **「指名測試」今天指得到的只有驗收情境**,那是今天的值域不是定義;
  日後別種測試也會是候選,不要把「指不出來」讀成「沒有任何測試」。
* **散文的指名有損。** 範圍寫法(某某到某某)與「情境 + 架構規則」混在同一格的部分,
  關聯表吃不下,轉寫時改記在 ladder_note 的本文裡 —— 計數看不到那一半。"""


def report(db_path: Path) -> int:
    conn = sqlite3.connect(db_path)
    try:
        total, with_test, with_enforcement, crossing = conn.execute(COUNTS_SQL).fetchone()

        print(f"\n=== 領域契約分診:{db_path.name} ===")
        if total == 0:
            print("\n  ⚠️ 契約:0 條 → **本次不適用(不是通過)**")
            print("     這份 store 沒有 domain_contracts 那一段。選填的區塊沒填,"
                  "不能折進通過的計數 —— 守衛沒有壞掉,是不再適用了,"
                  "而不適用不會有人發現。")
            return 3

        print(f"契約:{total} 條")
        print(f"  有指名測試的:{with_test} 條;指不出任何測試的:{total - with_test} 條")
        print(f"  宣稱有機械檢查的(enforcement <> none):{with_enforcement} 條"
              f"  ← 值域今天只有 none,所以這個數字必然是 0")
        print(f"  在自己那個物件內守不住的(跨聚合根):{crossing} 條")

        print("\n--- 分診佇列一:守不住的契約(crosses_aggregate = 1)---")
        rows = conn.execute(CROSSING_SQL).fetchall()
        if not rows:
            print("  (空)—— 注意這只表示**沒有人標**,不表示每條都守得住。")
        for cid, kind, guarded_in, disposition in rows:
            print(f"\n  ⚠️ {cid}({kind})守在:{guarded_in}")
            print(f"      處置:{disposition}")

        print("\n--- 分診佇列二:指不出任何測試的契約 ---")
        rows = conn.execute(NO_TEST_SQL).fetchall()
        if not rows:
            print("  (空)")
        for cid, kind, reason in rows:
            print(f"\n  ⚠️ {cid}({kind})")
            print(f"      指不出來的理由:{reason}")

        print(LIMITS)
        return 1 if (crossing or total - with_test) else 0
    finally:
        conn.close()


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    db_path = Path(argv[1])
    if not db_path.exists():
        print(f"找不到 store:{db_path}(先跑 spec_store.py import)", file=sys.stderr)
        return 2
    return report(db_path)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
