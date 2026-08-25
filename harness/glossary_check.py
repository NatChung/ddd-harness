#!/usr/bin/env python3
"""詞彙表 ↔ 對外欄位名 的對譯檢查 —— 「差幾個、差哪幾個」。

票 08-A 買到的東西就是這支能跑:**規格層寫著「實作命名必須照此詞彙表」,
而在這支之前沒有任何一步會去讀那句話。** 這裡把它變成一個查得出來的差額。

⚠️ **這支是第 2 階報告,不是 FK。** 硬擋只拿得到「匯入失敗」四個字,
   拿不到「差幾個」—— 而這張票的價值就在那個數字。

⚠️ **這支不掃任何識別字,也不檢查實作的類別 / 方法 / 變數名。**
   那要靠一種命名類的規則,而那個判定還沒拍板(票 08-B)。

⚠️ **「不適用」不算「通過」**(ADR 0005 §6),而且不適用有**兩種**:
   詞彙表是空的、或詞彙表有東西而這份 store 根本沒有對外合約可比。
   兩種都自成一類、印在最上面、給自己的離開碼。

離開碼:
    0  每個對外欄位都對得到詞,而且沒有詞宣稱一個合約裡不存在的欄位
    1  有對不到的、或有詞宣稱了合約沒有的欄位(要人去看)
    2  用法錯誤
    3  **不適用** —— 不是通過

用法:
    python3 glossary_check.py <spec.db>
"""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

# 詞裡面的英文識別字。中英並列的詞(中文名 + 英文名寫在同一格)靠這個抓得出英文那半。
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

TERMS_SQL = "SELECT term, wire_field FROM glossary_term ORDER BY seq"

BANNED_SQL = """
SELECT banned, use_instead, no_replacement_note, note
FROM glossary_banned_synonym
ORDER BY seq
"""

LIST_FIELDS_SQL = "SELECT field FROM wire_list_field ORDER BY field"

REQUEST_FIELDS_SQL = """
SELECT req_customer_field, req_items_field, req_product_field,
       req_quantity_field, req_price_field, req_currency_field, req_total_field
FROM wire_contract WHERE id = 1
"""

LIMITS = """
--- 這份檢查的上限(讀之前先看)---
* **「對得到一個詞」不等於「對到的是正確的那個詞」。** 中文詞 ↔ 英文識別字的對譯
  **沒有唯一解** —— 它是寫規格的人**選**的,不是推導出來的。這支驗得了前者,驗不了後者。
* **撞名不是對譯。** 「詞本身就含那個識別字」只在詞彙表本來就用英文識別字寫的時候會亮;
  中文寫的詞**永遠**走不到那條路。**撞得到 ≠ 這份規格做了對譯**。
* **這支不掃識別字,所以禁用同義詞只是一份查得到的清單,不是判決。**
  英文字根會撞:同一個字根出現在兩種識別字裡都可能是對的,掃出來會**懲罰寫得好的那一方**。
* **「類別名必須來自清單」對不上「一個詞可以有多個類別」。** 一個領域詞在實作裡可以正當地
  長出好幾個類別(本體 / 明細 / 儲存介面 / 進出口)。白名單比對會把正當的衍生名判成違規
  —— **所以這支一個類別名都不看**。
* **「對外欄位名」空白裝得下三種情況**:這個詞真的不上線 / 散文那一格寫的不是欄位名 /
  這份詞彙表根本沒有這一欄。**計數分不開這三種**,所以下面逐個印,不只印數量。"""


def _tokens(term: str) -> set[str]:
    return {m.group(0).lower() for m in IDENTIFIER.finditer(term)}


def _classify(fields: list[str], terms: list[tuple[str, str | None]]):
    """每個欄位對得到什麼。回傳 (欄位, 路徑, 對到的詞) 三元組。"""
    declared = {w: t for t, w in terms if w}
    by_token: dict[str, str] = {}
    for term, _ in terms:
        for token in _tokens(term):
            by_token.setdefault(token, term)

    out = []
    for field in fields:
        if field in declared:
            out.append((field, "宣告對譯", declared[field]))
        elif field.lower() in by_token:
            out.append((field, "撞名", by_token[field.lower()]))
        else:
            out.append((field, None, None))
    return out


def _print_block(title: str, rows) -> int:
    """印一段對譯結果,回傳對不到的個數。"""
    print(f"\n--- {title} ---")
    if not rows:
        print("  (這份合約沒有這一側的欄位)")
        return 0
    misses = [r for r in rows if r[1] is None]
    hits = [r for r in rows if r[1] is not None]
    print(f"  {len(rows)} 個欄位:對得到 {len(hits)} 個、**對不到 {len(misses)} 個**")
    for field, route, term in rows:
        if route is None:
            print(f"    ❌ {field} —— 對不到詞彙表的任何一個詞")
        else:
            print(f"    ✅ {field} —— {route}:{term}")
    return len(misses)


def report(db_path: Path) -> int:
    conn = sqlite3.connect(db_path)
    try:
        terms = conn.execute(TERMS_SQL).fetchall()
        list_fields = [r[0] for r in conn.execute(LIST_FIELDS_SQL).fetchall()]
        req_row = conn.execute(REQUEST_FIELDS_SQL).fetchone()
        req_fields = [f for f in (req_row or ()) if f]

        print(f"\n=== 詞彙表 ↔ 對外欄位名 對譯檢查:{db_path.name} ===")

        # 不適用,自成一類,印在最上面。**不准折進通過的計數。**
        if not terms:
            print("\n  ⚠️ 詞彙表:0 條 → **對譯檢查本次不適用(不是通過)**")
            print("     這份 store 沒有 glossary_terms 那一段。選填的區塊沒填,"
                  "不能折進通過的計數 —— 守衛沒有壞掉,是不再適用了,"
                  "而不適用不會有人發現。")
            return 3
        if not list_fields and not req_fields:
            print(f"\n  ⚠️ 詞彙表:{len(terms)} 條,而**對外合約 0 份** → "
                  "**對譯檢查本次不適用(不是通過)**")
            print("     這是第二種不適用,而且比第一種難看見:**詞彙表有東西**,"
                  "所以計數上什麼都不缺,只是沒有對面可以比。"
                  "有詞彙表不等於這條檢查跑過了。")
            return 3

        declared = [t for t in terms if t[1]]
        print(f"\n詞彙表:{len(terms)} 條")
        print(f"  宣告了對外欄位名的:{len(declared)} 條;"
              f"空白的:{len(terms) - len(declared)} 條"
              f"  ← 空白裝得下三種情況,見文末上限")

        misses = 0
        misses += _print_block(
            "對譯檢查(列表欄位)", _classify(list_fields, terms))
        misses += _print_block(
            "對譯檢查(請求側欄位)", _classify(req_fields, terms))

        # 反向:詞彙表宣稱某個詞上線,而合約裡沒有那個欄位。
        on_wire = set(list_fields) | set(req_fields)
        # ⚠️ 這一段**算進離開碼**。只印不算的警告 = 一個永遠 gate 不住任何東西的警告,
        #    而那正是本線一再量到的失效形狀:**寫在該寫的地方 ≠ 接上了。**
        orphan = [(t, w) for t, w in terms if w and w not in on_wire]
        print("\n--- 反向:詞彙表宣稱上線、而合約沒有這個欄位 ---")
        if not orphan:
            print("  (空)")
        for term, wire_field in orphan:
            print(f"    ⚠️ {term} → {wire_field}(合約裡沒有這個欄位)")

        banned = conn.execute(BANNED_SQL).fetchall()
        print(f"\n--- 禁用同義詞:{len(banned)} 列"
              f"(**查得到的清單,不是判決** —— 這支不掃任何識別字)---")
        if not banned:
            print("  (空)—— 注意這只表示**沒有人寫**,不表示沒有同義詞在流通。")
        for phrase, use_instead, no_replacement, note in banned:
            if use_instead:
                print(f"    禁用「{phrase}」→ 一律改用「{use_instead}」({note})")
            else:
                print(f"    禁用「{phrase}」→ 沒有替代詞:{no_replacement}({note})")

        print(LIMITS)
        return 1 if (misses or orphan) else 0
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
