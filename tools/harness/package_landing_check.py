#!/usr/bin/env python3
"""package 落點檢查 —— 規格宣告過的 package,實作產出裡真的有 class 嗎?

生成的 ArchUnit 規則照規格宣告的 package 名寫死(`architecture_rule` 的三張參數子表:
`forbidden_dependency` / `forbidden_annotation` / `forbidden_return_type`),
而 `ArchitectureTest.java` 每條規則都帶 `allowEmptyShould(true)`。兩件事接起來:

    agent 只要把 class 放到別的 package,整套架構檢查就全部靜靜地不適用
    —— 不是紅、不是報錯,是**綠**,而且看起來跟「完全遵守架構規則」一模一樣。

跟 `schema.sql` 對 `res_total_field` 的警語逐字同一種病:
**守衛沒有壞掉,是不再適用了,而不適用不會有人發現。**

風險是真的:凍結骨架用 `com.shop.domain` / `com.shop.usecase`,訪談那份 §10 用
`order/domain` / `order/application` / `order/adapter` —— **兩套本來就對不上**。

判準**刻意寫笨**(寫成「大致上有照著分層」這支就白做了):

    store 裡宣告過的每一個**自有** package,`src_root` 底下必須至少有一個 class
    的 `package` 宣告落在它(或它的子 package)裡。

沒有的話報「**不適用**」——**不算通過**,自成一類、印在報表最上面
(ADR 0005 §6 那條規矩,ADR 0006 §1 沿用、§3 定案)。

⚠️ **掃源碼樹,不掃編譯產出。** 編譯產出(`build/classes/**`)才是 ArchUnit 真正讀的
   東西,照理更忠實 —— 但它**不在的時候,「掃不到 class」跟「還沒 build」長得一模一樣**,
   而那正是這支要抓的那種病的翻版:不適用偽裝成乾淨。源碼樹永遠在,少一個假綠燈的來源。
   代價寫在報表的上限裡:這支證不了那些 class 編得起來。

⚠️ **package 取自檔案裡的 `package X;` 宣告,不是目錄路徑。** 宣告才是編譯器與 ArchUnit
   認的那個;目錄擺錯而宣告對的檔案,javac 也照樣接受(只是慣例上不這麼做)。

⚠️ **`--root` 打錯會讓這支什麼都沒查到**(2026-08-18 記下、票 14 補上)。
   `--root com.shopp`(多一個 p)→ 每一個自有 package 都不落在 root 底下 →
   全被歸進「第三方,不檢查」→ 空的 0 個 → **離開碼從 1 翻成 0**。
   上限段本來就寫著「排除清單是最大的假通過來源」,但**沒說離開碼會翻綠**,
   而翻綠才是會騙到人的那半。現在:**自有 package 一個都沒有 = 這次什麼都沒檢查到
   → 離開碼 3(整份不適用)**,不是 0。同一條也蓋掉 root 推導成空字串的情況。

離開碼:
    0  宣告過的自有 package 全部都有 class
    1  **有空的 → 不適用,不算通過**
    2  用法錯誤 / 吃錯目錄 / spec 沒過驗證
    3  **檢查本身不適用 —— 一個 package 都沒被檢查到。** 三種成因:
       (a) 這份 store 一條 package 都沒宣告;
       (b) root 沒對上任何一條宣告(`--root` 打錯、或推導出空 root)——
           宣告全被當成第三方放走了;
       (c) 宣告全是含萬用字元的 pattern,這支比不了。
       三種都**不是通過**。

用法:
    python3 package_landing_check.py <src_root> <spec.yaml> [<spec2.yaml> …] [--root com.shop]
"""

from __future__ import annotations

import re
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from spec_store import SpecError, build_store, load_specs  # noqa: E402

# 三張參數子表裡每一個裝 package 名的欄位。**加新的 rule kind 就要在這裡加一段** ——
# 否則那個 kind 宣告的 package 不會被這支蓋到,而「沒被蓋到的宣告」正是本支存在的理由。
#
# role 只影響**解釋**,不影響判定:
#   from       規則的來源側。空 → ArchUnit 掃不到任何 class → 配上 allowEmptyShould(true)
#              **整條規則必然綠**。這是最危險的一種空。
#   to / annotation / return
#              規則的禁止目標側。空 → 規則還在跑,只是那個目標不存在,那一半約束是空的。
DECLARED_SQL = """
SELECT rule_id, from_package,       'from'       FROM forbidden_dependency
UNION ALL
SELECT rule_id, to_package,         'to'         FROM forbidden_dependency
UNION ALL
SELECT rule_id, from_package,       'from'       FROM forbidden_annotation
UNION ALL
SELECT rule_id, annotation_package, 'annotation' FROM forbidden_annotation
UNION ALL
SELECT rule_id, from_package,       'from'       FROM forbidden_return_type
UNION ALL
SELECT rule_id, return_package,     'return'     FROM forbidden_return_type
"""

# `package com.shop.domain;` —— 行首(容許縮排)、不吃註解掉的那種。
PACKAGE_DECL = re.compile(r"^\s*package\s+([A-Za-z_$][\w$]*(?:\s*\.\s*[A-Za-z_$][\w$]*)*)\s*;", re.M)

# 「這個檔案裡有沒有型別宣告」。只求粗:一個只有 license 註解的 .java 不該被算成一個 class。
TYPE_DECL = re.compile(r"\b(?:class|interface|enum|record|@interface)\s+[A-Za-z_$]")

# ArchUnit 的 package pattern 支援萬用字元(`com.*.domain..`)。schema 的 CHECK 只逼 `%..`,
# 所以寫得出來。這支比不了 —— **比不了就丟進「不適用」,絕不當成通過。**
WILDCARD = re.compile(r"[*?]")

# 不是 class 的 .java:package-info 只掛 package annotation,module-info 是模組宣告。
NOT_A_CLASS = {"package-info.java", "module-info.java"}


# ── package pattern 的比對 ───────────────────────────────────────────────

def base_of(pattern: str) -> str:
    """`com.shop.domain..` → `com.shop.domain`。"""
    return pattern[:-2] if pattern.endswith("..") else pattern


def covers(pattern: str, package: str) -> bool:
    """`package` 落在 `pattern` 裡嗎?

    **大小寫敏感**(Java package 就是),而且**卡點號邊界**:

      * `com.shop.domain`        ✅ 自己算
      * `com.shop.domain.order`  ✅ 子 package 算
      * `com.shop`               ❌ 上層**不算** —— 凍結骨架的 Application 就住這裡,
                                    寫成無邊界字串前綴的話它會把三個空 package 全部
                                    假通過掉,而那是這支最容易寫出來的 bug。
      * `com.shop.domainhelper`  ❌ 邊界不對
    """
    base = base_of(pattern)
    return package == base or package.startswith(base + ".")


def derive_root(from_packages: list[str]) -> str:
    """自有 package 的 root = `from` 側各值的**點號分段**共同前綴。

    為什麼只看 `from` 側:每一條規則的 `from` 都是「本案自己的某一層」——
    沒有人會把第三方 package 寫進 from。而 `to` / `annotation` / `return` 側
    **兩種都有**(`com.shop.adapter..` 與 `org.springframework..` 並存),
    需要一個判準把它們分開。

    分段而不是字串前綴:`com.shop.domain` 與 `com.shopping.x` 的字串共同前綴是
    `com.shop`,那是一個**假 root**,會把 `com.shopping.x` 誤收成自有。

    ⚠️ **已知的洞**:from 側只有一個值時,root = 那整個 package(例如 `com.shop.domain`),
       於是 `to` 側的 `com.shop.adapter..` 會被歸成「第三方」而不被檢查 ——
       **空著也不會被報,是假通過**。所以報表逐個印出被排除的 package,
       並要人看過;不對就用 `--root` 蓋掉。
    """
    segs = [base_of(p).split(".") for p in from_packages if p]
    if not segs:
        return ""
    common = segs[0]
    for s in segs[1:]:
        i = 0
        while i < min(len(common), len(s)) and common[i] == s[i]:
            i += 1
        common = common[:i]
    return ".".join(common)


def rule_key(rule_id: str) -> tuple[str, int, str]:
    """`A2` 要排在 `A10` 前面 —— 字典序會給出 A1、A10、A2,讀報表的人會以為漏了。"""
    m = re.match(r"^([A-Za-z]*)(\d+)(.*)$", rule_id)
    return (m.group(1), int(m.group(2)), m.group(3)) if m else (rule_id, 0, "")


# ── 掃源碼樹 ─────────────────────────────────────────────────────────────

DEFAULT_PACKAGE = "(default)"


def scan_sources(src_root: Path) -> dict[str, list[str]]:
    """`{package: [class 名]}`。

    **一個 `.java` 檔算一個 class**,以檔名為名。不解析檔案內的巢狀型別或多個
    top-level 型別 —— 這支問的是「這個 package 空不空」,而「一個檔就不空了」。
    (上限印在報表裡。)
    """
    if not src_root.is_dir():
        # ⚠️ 離開碼**必須是 2,不是 1**。1 是「宣告過的 package 空著」那個判定,
        #    而「目錄根本不在」是這支**沒跑起來** —— 混在一起的話,吃錯路徑會被
        #    讀成「實作把 package 放光了」:檢查沒跑,卻回報了它存在的理由那個結論。
        #    (跟 SpecError 回 2 而不是 3 同一條分界。)
        print(
            f"找不到 {src_root} —— 這支要吃實作的原始碼根目錄(例:.../src/main/java)",
            file=sys.stderr,
        )
        raise SystemExit(2)
    found: dict[str, list[str]] = {}
    for path in sorted(src_root.rglob("*.java")):
        if path.name in NOT_A_CLASS:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if not TYPE_DECL.search(text):
            continue
        m = PACKAGE_DECL.search(text)
        pkg = re.sub(r"\s+", "", m.group(1)) if m else DEFAULT_PACKAGE
        found.setdefault(pkg, []).append(path.stem)
    return found


# ── 判定 ─────────────────────────────────────────────────────────────────

def check(src_root: Path, spec_paths: list[str | Path]) -> dict:
    """回傳報表用的資料。**「不適用」自成一類,絕不折進通過。**"""
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "spec.db"
        build_store(db, load_specs(list(spec_paths)))
        conn = sqlite3.connect(db)
        try:
            rows = conn.execute(DECLARED_SQL).fetchall()
        finally:
            conn.close()
    return judge(src_root, rows)


def judge(src_root: Path, rows: list[tuple[str, str, str]], root: str | None = None) -> dict:
    """把 `(rule_id, package, role)` 三元組跟源碼樹對起來。db 與檔案分開,才測得動。"""
    classes = scan_sources(src_root)

    # 去重:`forbidden_dependency` 一條規則有幾個 to_package 就有幾列,
    # 每一列都帶同一個 from_package —— 不去重的話報表會印出 A1(from) 四次。
    declared: dict[str, set[tuple[str, str]]] = {}
    for rule_id, pattern, role in rows:
        declared.setdefault(pattern, set()).add((rule_id, role))

    from_packages = sorted({p for p, uses in declared.items() if any(r == "from" for _, r in uses)})
    derived = derive_root(from_packages)
    root_used = root if root is not None else derived

    owned: list[dict] = []
    external: list[dict] = []
    unmatchable: list[dict] = []
    for pattern in sorted(declared):
        entry = {
            "pattern": pattern,
            "uses": sorted(declared[pattern], key=lambda u: (rule_key(u[0]), u[1])),
            "rules": sorted({rid for rid, _ in declared[pattern]}, key=rule_key),
            "from_rules": sorted(
                {rid for rid, role in declared[pattern] if role == "from"}, key=rule_key
            ),
        }
        if WILDCARD.search(pattern):
            unmatchable.append(entry)
            continue
        if not (root_used and covers(root_used + "..", base_of(pattern))):
            external.append(entry)
            continue
        hits = {pkg: names for pkg, names in classes.items() if covers(pattern, pkg)}
        entry["packages"] = dict(sorted(hits.items()))
        entry["class_count"] = sum(len(v) for v in hits.values())
        owned.append(entry)

    empty = [e for e in owned if e["class_count"] == 0]
    filled = [e for e in owned if e["class_count"] > 0]

    # 宣告外的 package:有 class,卻沒被任何**自有**宣告蓋到。只印,不進判定。
    undeclared = {
        pkg: names for pkg, names in sorted(classes.items())
        if not any(covers(e["pattern"], pkg) for e in owned)
    }

    # from 側落在空 package 的規則 = 整條必然綠(allowEmptyShould(true))。
    vacuous_rules = sorted({rid for e in empty for rid in e["from_rules"]}, key=rule_key)
    weakened_rules = sorted(
        {rid for e in empty for rid, role in e["uses"] if role != "from"} - set(vacuous_rules),
        key=rule_key,
    )

    return {
        "src_root": src_root,
        "root_used": root_used,
        "root_derived": derived,
        "root_overridden": root is not None and root != derived,
        "declared_total": len(declared),
        "owned": owned,
        "empty": empty,
        "filled": filled,
        "external": external,
        "unmatchable": unmatchable,
        "undeclared": undeclared,
        "vacuous_rules": vacuous_rules,
        "weakened_rules": weakened_rules,
        "classes_total": sum(len(v) for v in classes.values()),
    }


LIMITS = """
--- 這支檢查的上限(讀結論之前先看)---
* ⚠️ **它只看「package 裡有沒有 class」,不看那些 class 對不對。** 在宣告過的 package
  裡放一個空的 `Placeholder.java` 就能讓這支全綠 —— 它證明的是**落點存在**,
  不證明那裡的東西是領域模型。跟內圈落點檢查那條上限同型:**形式滿足得了**。
* **掃源碼樹,不掃編譯產出** —— 它證不了那些 class 編得起來,而 ArchUnit 讀的是 `.class`。
  一個語法錯的檔案在這支眼裡照樣算「有 class」。
* **一個 `.java` 檔算一個 class**(以檔名為名),不解析檔案內的巢狀型別或多個 top-level 型別。
  `package-info.java` / `module-info.java` 不算 class;沒有型別宣告的檔案不算。
* **比對是機械的、大小寫敏感的、卡點號邊界的**:`com.shop.domain..` 去掉尾巴之後,
  `pkg == com.shop.domain` 或 `pkg` 以 `com.shop.domain.` 開頭才算。
  **`com.shop` 不算在 `com.shop.domain..` 裡**;`com.shop.Domain`、`com.shop.domainhelper` 也不算。
* **含萬用字元的 pattern 比不了** → 丟進「不適用」,**絕不當通過**。
* ⚠️ **排除清單(上面「不檢查」那段的第三方 package)是這支最大的假通過來源。** root 推導錯 →
  某個自有 package 被歸成第三方 → 它空著也不會被報。**逐個看過**,不對就用 `--root` 重跑。
  (**root 錯到一個都沒對上**時,離開碼是 3 不是 0 —— 但只錯掉**一部分**的話,
  剩下的照樣判定,離開碼看得起來很正常。那一半只有讀這份清單才發現得了。)
* **「宣告外的 package」只印,不進判定。** 把 class 放到別的 package 不是這條的違規,
  但它是「宣告過的 package 空著」**最常見的成因**,所以印在旁邊。"""


def _fmt(xs: list[str]) -> str:
    return "、".join(xs) if xs else "(無)"


def report(rep: dict) -> int:
    print(f"\n=== package 落點檢查:{rep['src_root']} ===")
    print("判準:store 裡宣告過的每個自有 package,原始碼裡要有至少一個 class 的 "
          "`package` 宣告落在它(或它的子 package)裡。\n")

    if rep["declared_total"] == 0:
        # 「找不到東西所以沒問題」是最廉價的假綠燈。
        print("  ⚠️ 宣告過的 package:0 個 → **本次不適用(不是通過)**")
        print("     這份 store 的三張參數子表都是空的(沒有任何 enforcement 是 archunit_*),"
              "沒有 package 可比 —— 不能折進通過的計數。")
        print(LIMITS)
        return 3

    src = "、".join(f"{p}({len(v)})" for p, v in sorted(rep["undeclared"].items())) or ""
    print(f"自有 package 的 root:**{rep['root_used'] or '(空)'}**"
          + ("(--root 指定)" if rep["root_overridden"]
             else f"(從 from 側推導,原始推導值 {rep['root_derived'] or '(空)'})"))
    print(f"宣告過的 package:{rep['declared_total']} 個"
          f"(自有 {len(rep['owned'])}、第三方 {len(rep['external'])}、"
          f"比不了 {len(rep['unmatchable'])});原始碼共 {rep['classes_total']} 個 class。")

    if not rep["owned"]:
        # 宣告過 package,卻一個都沒進「自有」——**這次一個 package 都沒被檢查到**。
        # 舊版在這裡會走完整份報表:空的 0 個 → return 0 → **翻綠**。
        # 「找不到東西所以沒問題」是最廉價的假綠燈。
        print("\n  ❌ **自有 package = 0 個 —— 這不是乾淨,是這次一個 package 都沒檢查到。**")
        if rep["external"]:
            print(f"     宣告過的 {len(rep['external'])} 個 package 全部落在 root "
                  f"`{rep['root_used'] or '(空)'}` 之外,被歸成第三方放走了:")
            for e in rep["external"]:
                print(f"       · `{e['pattern']}`(由 {_fmt(e['rules'])} 宣告)")
            if rep["root_overridden"]:
                print(f"     ⚠️ root 是 `--root` 指定的。**打錯了嗎?** 從 from 側推導出來的是 "
                      f"`{rep['root_derived'] or '(空)'}`。")
            elif not rep["root_derived"]:
                print("     ⚠️ 推導出來的 root 是**空的** —— from 側沒有值,"
                      "或各值之間沒有共同的點號分段前綴。用 `--root` 指定。")
        if rep["unmatchable"]:
            print(f"     另有 {len(rep['unmatchable'])} 個宣告含萬用字元,這支比不了:"
                  f"{_fmt([e['pattern'] for e in rep['unmatchable']])}")
        print("\n     **整份不適用,不是通過**(ADR 0005 §6)—— 離開碼 3,"
              "跟「宣告過的 package 空著」(1)、「吃錯目錄」(2)分得開。")
        print(LIMITS)
        return 3

    # ── 不適用印在最上面,自成一類(ADR 0005 §6)───────────────────────
    print("\n【不適用】—— 不是通過,這幾個 package 沒有任何 class,"
          "掛在它們身上的規則掃不到東西")
    if not rep["empty"] and not rep["unmatchable"]:
        print("  (無)")
    for e in rep["empty"]:
        roles = "、".join(f"{rid}({role})" for rid, role in e["uses"])
        print(f"  ◻ `{e['pattern']}` —— 0 個 class;宣告它的規則:{roles}")
    for e in rep["unmatchable"]:
        print(f"  ◻ `{e['pattern']}` —— 含萬用字元,這支比不了(**不是通過**);"
              f"宣告它的規則:{_fmt(e['rules'])}")

    if rep["empty"]:
        print(f"\n  ⚠️ **整條不適用的規則(from 側掃不到任何 class)**:"
              f"{_fmt(rep['vacuous_rules'])} —— 共 {len(rep['vacuous_rules'])} 條。")
        print("     配上 `allowEmptyShould(true)`,它們**必然綠**,"
              "而且綠得跟「完全遵守架構規則」一模一樣。")
        if rep["weakened_rules"]:
            print(f"  ⚠️ **禁止目標不存在的規則(to / annotation / return 側空)**:"
                  f"{_fmt(rep['weakened_rules'])} —— 規則還在跑,只是那一半約束是空的。")

    print(f"\n【通過】—— 宣告過而且真的有 class:**{len(rep['filled'])} 個 package**")
    if not rep["filled"]:
        print("  (無)")
    for e in rep["filled"]:
        where = "、".join(f"{p}({len(v)})" for p, v in e["packages"].items())
        print(f"  · `{e['pattern']}` —— {e['class_count']} 個 class:{where}")

    print(f"\n【不檢查:不在 root `{rep['root_used']}` 底下】"
          f"—— 第三方 package,{len(rep['external'])} 個")
    for e in rep["external"]:
        print(f"  · `{e['pattern']}`(由 {_fmt(e['rules'])} 宣告)")
    print("  ⚠️ **這份排除清單要逐個看過** —— 任何一個其實是本案自己的 package,"
          "它空著也不會被報。用 `--root` 重跑。")

    print(f"\n【參考,不進判定】有 class、卻沒被任何自有宣告蓋到的 package:"
          f"{len(rep['undeclared'])} 個")
    print(f"  {src or '(無)'}")
    print("  ⚠️ 這一段不影響上面的判定,但**「宣告過的 package 空著」最常見的成因就在這裡**:"
          "class 被放到了規格沒宣告的地方。")

    print(LIMITS)
    return 1 if (rep["empty"] or rep["unmatchable"]) else 0


def parse_argv(argv: list[str]) -> tuple[list[str], str | None]:
    """`--root com.shop` 與 `--root=com.shop` 兩種寫法都吃。不認得的 `--x` 直接掛。"""
    args: list[str] = []
    root: str | None = None
    it = iter(argv)
    for a in it:
        if a == "--root":
            root = next(it, None)
            if root is None:
                raise ValueError("--root 後面要接 package 名")
        elif a.startswith("--root="):
            root = a.split("=", 1)[1]
        elif a.startswith("--"):
            raise ValueError(f"不認得的選項:{a}")
        else:
            args.append(a)
    return args, root


def main(argv: list[str]) -> int:
    try:
        args, root = parse_argv(argv[1:])
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    if len(args) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "spec.db"
            build_store(db, load_specs(list(args[1:])))
            conn = sqlite3.connect(db)
            try:
                rows = conn.execute(DECLARED_SQL).fetchall()
            finally:
                conn.close()
        rep = judge(Path(args[0]), rows, root=root)
    except SpecError as exc:
        print("spec 本身沒過驗證,無從比對:", file=sys.stderr)
        for problem in exc.problems:
            print(f"  - {problem}", file=sys.stderr)
        return 2
    return report(rep)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
