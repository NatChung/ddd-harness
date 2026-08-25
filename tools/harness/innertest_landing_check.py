#!/usr/bin/env python3
"""內圈測試的落點檢查 —— store 裡每條契約,指得出至少一條內圈測試嗎?(票 13)

這是同一個形狀的第三次:票 05 答案落點(問題 → 下一輪的落點表)、票 11 package 落點
(宣告的 package → 真的有 class),這次是 **契約 → 內圈測試**。它只問「有沒有」,不判斷
好不好 —— 所以不會犯「懲罰寫得好的那一方」那個病(票 03 / 08 的假陽性家族)。
它也讓 2026-08-18 量到的 `enforcement = none 20/20` 第一次有東西可以動。

**宣告在測試檔頭,不在方法名**(票 13 「2026-08-25 · 形狀」第 1 條):
`src/innerTest/**/*.java` 每支 class 的 javadoc 帶 `@covers C8, C9`(契約編號)或
`@covers G16`(情境編號)。方法名帶編號那個舊約定(`void C4_…()`)**不算落點** ——
它逼人把編號塞進名字,而且一個方法只能掛一條;這支另印一行計數,讓舊約定的跑讀起來
是「舊約定」,不是「偷懶」。

⚠️ **編號從 store 讀,不寫死前綴。** 2026-08-19 那份規格的情境編號是 `G1`、`G16`,
   不是票裡舉例的 `S`;寫死 `C` / `S` 這支對那份 store 會整份漂。

三段分開印,**不合併計數**:

1. **落點**:每條契約有沒有內圈測試宣告 `@covers` 它。**契約決定離開碼**;情境只印參考 ——
   情境的落點是幕三生成的驗收(逐位元組驗過),要求每條情境也有內圈測試等於再犯一次
   「懲罰寫得好的那一方」。
2. **反向**:每個 `@covers` 指到的編號,在 store 裡存不存在。指了不存在的契約 = 漂(打字錯、
   或規格改了編號而測試沒跟)。認不出來的寫法、宣告在錯的位置(方法 javadoc / 行註解)也列這裡。
3. **打在哪個入口**:印 `第 4 階,人讀` —— 列出每支測試檔裡出現的 `Type.method(`、`new Type(`、
   `Type.class` 三種 token,**不判斷**。票 13 陽性一(`Order.restore` 被 `!isStatic` 濾掉)
   這一欄抓不到,只能讓人看得見那支測試用了 `Order.class` 反射。

副(恆真分診)**不在這支裡跑**:仍交 `vacuous_tests.py`(要 PIT 的 mutation matrix)。
這支只印一段固定提醒,講第三類「範圍不足」兩支都抓不到。

離開碼:
    0  每條契約都有 `@covers`,而且沒有任何宣告指到 store 沒有的編號
    1  任一契約無落點;或任一 `@covers` 漂(指到不存在的編號 / 認不出來 / 位置不對)。
       **目錄在但零個 `.java`、或有檔但零個 `@covers` → 1,不是 3**:`run_act4.sh` 自己會
       `mkdir -p src/innerTest/java`,所以「目錄在、空的」正是「agent 一條內圈測試都沒寫」
       的長相 —— 那是漏,不是不適用(跟 `landing_check` 對齊)。
    2  用法錯誤(store 不在 / workdir 不在)
    3  **不適用** —— 沒有 `src/innerTest/` 目錄(這個工作目錄沒經過 `run_act4.sh` 的注入),
       或 store 契約與情境都是 0 條(沒有東西可以落點)。**不是通過**,自成一類印最上面。

用法:
    python3 innertest_landing_check.py <spec.db> <workdir>
"""

from __future__ import annotations

import re
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path

INNER_REL = Path("src/innerTest")

CONTRACTS_SQL = "SELECT id, kind, guarded_in FROM domain_contract"
SCENARIOS_SQL = "SELECT id FROM acceptance_scenario"

# `/** … */` 一塊一塊抓;之後看它後面接的是不是型別宣告(見 `_is_type_javadoc`)。
JAVADOC = re.compile(r"/\*\*(.*?)\*/", re.S)
# javadoc 與型別宣告之間允許的東西:空白、annotation(可帶括號參數)、修飾詞。
BETWEEN = re.compile(
    r"^(?:\s|@\w+(?:\([^)]*\))?)*"
    r"(?:(?:public|protected|private|final|abstract|static|sealed|non-sealed|strictfp)\s+)*"
    r"(?:class|interface|enum|record|@interface)\s+[A-Za-z_$]"
)
TYPE_NAME = re.compile(r"(?:class|interface|enum|record)\s+([A-Za-z_$][\w$]*)")

# `@covers C8, C9` —— 整行的其餘部分都是宣告;下一行不接續。
COVERS_LINE = re.compile(r"@covers\b(.*)$", re.M)
ID_TOKEN = re.compile(r"^[A-Za-z]+\d+$")
SPLIT = re.compile(r"[,、;\s]+")

# 舊約定:方法名帶編號(`void C4_單價…()`)。只計數,不算落點。
OLD_CONVENTION = re.compile(r"\bvoid\s+([A-Z]+\d+)_[\w$]*\s*\(")

# 第三段的三種 token(掃的是去掉註解與字串之後的原始碼)。
QUALIFIED_CALL = re.compile(r"\b([A-Z][\w$]*)\s*\.\s*([a-z][\w$]*)\s*\(")
NEW_CALL = re.compile(r"\bnew\s+([A-Z][\w$]*)\s*[(<]")
CLASS_LITERAL = re.compile(r"\b([A-Z][\w$]*)\s*\.\s*class\b")
# 全大寫加底線的是常數(`THE_ONLY_ALLOWED_MUTATOR`),不是型別;Java 型別名是 CamelCase。
CONSTANT = re.compile(r"^[A-Z][A-Z0-9_]+$")
COMMENTS_AND_STRINGS = re.compile(
    r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"', re.S
)


@dataclass
class TestFile:
    rel: str                                  # 相對 workdir
    type_names: list[str] = field(default_factory=list)
    covers: list[str] = field(default_factory=list)          # class javadoc 裡認得出來的編號(去重、保序)
    unrecognised: list[str] = field(default_factory=list)    # `@covers` 後面認不出來的 token
    misplaced: list[str] = field(default_factory=list)       # 不在 class javadoc 裡的 `@covers` 行(原文)
    old_convention: list[str] = field(default_factory=list)  # 舊約定方法名帶的編號
    calls: dict[str, list[str]] = field(default_factory=dict)  # Type → [method…]
    news: list[str] = field(default_factory=list)
    class_literals: list[str] = field(default_factory=list)


# ── 讀 store ────────────────────────────────────────────────────────────

def load_ids(db_path: Path) -> tuple[list[tuple[str, str, str]], list[str]]:
    conn = sqlite3.connect(db_path)
    try:
        contracts = conn.execute(CONTRACTS_SQL).fetchall()
        scenarios = [r[0] for r in conn.execute(SCENARIOS_SQL).fetchall()]
    finally:
        conn.close()
    return sorted(contracts, key=lambda r: id_key(r[0])), sorted(scenarios, key=id_key)


def id_key(cid: str) -> tuple[str, int, str]:
    """`C2` 排在 `C10` 前面 —— 字典序會給出 C1、C10、C2,讀報表的人會以為漏了。"""
    m = re.match(r"^([A-Za-z]*)(\d+)(.*)$", cid)
    return (m.group(1), int(m.group(2)), m.group(3)) if m else (cid, 0, "")


# ── 掃內圈測試 ──────────────────────────────────────────────────────────

def _is_type_javadoc(text: str, end: int) -> bool:
    """這塊 javadoc 後面接的是型別宣告嗎?(不是的話它是方法 / 欄位的 javadoc。)"""
    return BETWEEN.match(text[end:]) is not None


def parse_covers(line_rest: str) -> tuple[list[str], list[str]]:
    """`@covers` 後面那段 → (認得出來的編號, 認不出來的 token)。"""
    ok: list[str] = []
    bad: list[str] = []
    for tok in SPLIT.split(line_rest.strip()):
        tok = tok.strip("().:*")
        if not tok:
            continue
        (ok if ID_TOKEN.match(tok) else bad).append(tok)
    return ok, bad


def parse_test_file(path: Path, workdir: Path) -> TestFile:
    text = path.read_text(encoding="utf-8", errors="replace")
    tf = TestFile(rel=str(path.relative_to(workdir)))

    seen_spans: list[tuple[int, int]] = []
    for m in JAVADOC.finditer(text):
        body = m.group(1)
        if _is_type_javadoc(text, m.end()):
            seen_spans.append((m.start(), m.end()))
            for cm in COVERS_LINE.finditer(body):
                ok, bad = parse_covers(cm.group(1))
                for cid in ok:
                    if cid not in tf.covers:
                        tf.covers.append(cid)
                tf.unrecognised.extend(bad)
    # 不在 class javadoc 裡的 `@covers`(方法 javadoc、行註解、字串)—— 位置不對,不算落點。
    for cm in COVERS_LINE.finditer(text):
        if not any(s <= cm.start() < e for s, e in seen_spans):
            tf.misplaced.append(cm.group(0).strip()[:60])

    tf.type_names = TYPE_NAME.findall(COMMENTS_AND_STRINGS.sub(" ", text))
    tf.old_convention = OLD_CONVENTION.findall(text)

    code = COMMENTS_AND_STRINGS.sub(" ", text)
    for t, meth in QUALIFIED_CALL.findall(code):
        if CONSTANT.match(t):
            continue   # `THE_ONLY_ALLOWED_MUTATOR.equals(` 是常數不是型別
        tf.calls.setdefault(t, [])
        if meth not in tf.calls[t]:
            tf.calls[t].append(meth)
    tf.news = sorted(set(NEW_CALL.findall(code)))
    tf.class_literals = sorted(set(CLASS_LITERAL.findall(code)))
    return tf


def scan_inner_tests(workdir: Path) -> list[TestFile] | None:
    """回 None = 沒有 `src/innerTest/` 目錄(不適用);回 [] = 目錄在、零個 .java(漏)。"""
    root = workdir / INNER_REL
    if not root.is_dir():
        return None
    return [parse_test_file(p, workdir) for p in sorted(root.rglob("*.java"))]


# ── 判定 ────────────────────────────────────────────────────────────────

def judge(contracts: list[tuple[str, str, str]], scenarios: list[str],
          files: list[TestFile] | None, workdir: Path) -> dict:
    known = {c[0] for c in contracts} | set(scenarios)
    landing: dict[str, list[str]] = {cid: [] for cid in known}
    drift: list[tuple[str, str]] = []          # (檔, 指到不存在的編號)
    unrecognised: list[tuple[str, str]] = []
    misplaced: list[tuple[str, str]] = []
    for tf in files or []:
        for cid in tf.covers:
            if cid in landing:
                landing[cid].append(tf.rel)
            else:
                drift.append((tf.rel, cid))
        unrecognised.extend((tf.rel, t) for t in tf.unrecognised)
        misplaced.extend((tf.rel, t) for t in tf.misplaced)

    unlanded = [c for c in contracts if not landing[c[0]]]
    return {
        "workdir": workdir,
        "contracts": contracts,
        "scenarios": scenarios,
        "files": files,
        "landing": landing,
        "unlanded": unlanded,
        "drift": drift,
        "unrecognised": unrecognised,
        "misplaced": misplaced,
        "old_convention_total": sum(len(tf.old_convention) for tf in files or []),
        "declaring_files": sum(1 for tf in files or [] if tf.covers),
    }


LIMITS = """
--- 這支檢查的上限(讀結論之前先看)---
* ⚠️ **`@covers` 是一條約定。** 隨便一支測試在檔頭寫 `@covers C1` 就通過 —— 它只證明
  **落點存在**,不證明那條測試真的在驗 C1。跟 package 落點檢查同型:**形式滿足得了**。
* **「打在哪個入口」那欄是第 4 階,人讀。** 它列的是 token,不是呼叫圖:靜態工廠、
  建構子、`.class` 反射列得出來,實例方法(`order.changeStatusTo(…)`)列不出來。
  票 13 陽性一(守 C8 的測試用 `!isStatic` 把 `Order.restore` 濾掉)這一欄**抓不到**,
  只能讓人看到那支測試用了 `Order.class`。
* **第三類「範圍不足」兩支都抓不到。** 落點檢查看不到(落點存在、命名正確、而且綠),
  `vacuous_tests` 也看不到(它不是恆真 —— 加一個 public 實例 mutator 它會紅)。第 4 階。
* **舊約定(方法名帶編號)只計數,不算落點。** 舊 run 整份無落點是預期的,不是那跑偷懶。
* **契約決定離開碼,情境只印參考。** 情境的落點在幕三生成的驗收;內圈 `@covers G16`
  是額外宣告,合法但不強制。
* **掃的是原始碼樹,不是編譯產出。** 一支編不過的測試檔在這裡照樣算宣告了。"""

VACUITY_NOTE = """
--- 副:恆真分診(這支不跑,交 `vacuous_tests.py`)---
  對內圈跑 PIT(`fullMutationMatrix=true`)後 `python3 vacuous_tests.py <mutations.xml>`,
  交的是**分診佇列不是判決** —— 它分不出「恆真」與「碰不到」。
  ⚠️ 第三類「範圍不足」**兩支都抓不到**,固定提醒:一支測試存在、宣告正確、而且綠,
     但它列舉的入口漏了半個 interface(票 13 陽性一:`!isStatic` 濾掉 `Order.restore`),
     或它的反例沒打到規格說要擋的那個值(票 13 陽性二:三條非法轉移都沒試 `null`)。
     這兩種要靠人讀第三段那欄,沒有機械檢查。"""


def _fmt(xs: list[str]) -> str:
    return "、".join(xs) if xs else "(無)"


def report(rep: dict) -> int:
    files = rep["files"]
    contracts, scenarios = rep["contracts"], rep["scenarios"]
    print(f"\n=== 內圈測試落點檢查:{rep['workdir']} ===")
    print("判準:store 裡每條契約,`src/innerTest/**/*.java` 至少一支 class 的 javadoc 要 "
          "`@covers` 它的編號。只證明落點存在,不證明那條測試真的在驗它。\n")

    # ── 不適用印在最上面,自成一類(ADR 0005 §6)─────────────────────────
    if files is None:
        print(f"  ⚠️ 沒有 `{INNER_REL}/` 目錄 → **整份不適用(不是通過)**")
        print("     這個工作目錄沒經過 `run_act4.sh` 的注入(它會 mkdir 那層),"
              "沒有內圈測試可以查 —— 離開碼 3,跟「有目錄但零宣告」(1)分得開。")
        print(LIMITS)
        return 3
    if not contracts and not scenarios:
        print("  ⚠️ store 契約 0 條、情境 0 條 → **整份不適用(不是通過)**")
        print("     沒有任何編號可以被 `@covers`,這次一條落點都沒查到 —— 離開碼 3。")
        print(LIMITS)
        return 3

    print(f"store:契約 {len(contracts)} 條、情境 {len(scenarios)} 條;"
          f"內圈測試檔 {len(files)} 支,其中檔頭帶 `@covers` 的 {rep['declaring_files']} 支;"
          f"舊約定方法名帶編號 {rep['old_convention_total']} 條(不算落點)。")
    if not files:
        print(f"  ❌ `{INNER_REL}/` 在,但**零個 .java** —— agent 一條內圈測試都沒寫。"
              "這是漏(每條契約無落點),不是不適用。")

    # ── 第一段:落點 ───────────────────────────────────────────────────
    print("\n--- 第一段:落點(契約逐條;決定離開碼)---")
    landing = rep["landing"]
    for cid, kind, guarded_in in contracts:
        where = landing[cid]
        mark = "✅" if where else "❌"
        tail = _fmt(where) if where else "**無落點**"
        print(f"  {mark} {cid}({kind})守在:{guarded_in} —— {tail}")
    landed = len(contracts) - len(rep["unlanded"])
    print(f"  小計:有落點 {landed} / {len(contracts)};無落點 {len(rep['unlanded'])} 條:"
          f"{_fmt([c[0] for c in rep['unlanded']])}")
    if scenarios:
        print("\n  情境(參考,不進判定 —— 它們的落點是幕三生成的驗收):")
        for sid in scenarios:
            where = landing[sid]
            print(f"    · {sid} —— {_fmt(where) if where else '(內圈沒宣告)'}")

    # ── 第二段:反向 ───────────────────────────────────────────────────
    print("\n--- 第二段:反向(每個 `@covers` 指到的編號,store 裡存不存在)---")
    drift, unrec, misplaced = rep["drift"], rep["unrecognised"], rep["misplaced"]
    if not (drift or unrec or misplaced):
        if rep["declaring_files"]:
            print("  (全部存在)")
        else:
            print("  (沒有任何宣告,所以沒有東西可以漂)")
    for rel, cid in drift:
        print(f"  ❌ `{cid}` ← {rel} —— store 裡沒有這個編號(打字錯,或規格改了編號而測試沒跟)")
    for rel, tok in unrec:
        print(f"  ❌ `{tok}` ← {rel} —— `@covers` 後面認不出來的寫法(要 `C8` / `G16` 這種)")
    for rel, line in misplaced:
        print(f"  ❌ `{line}` ← {rel} —— `@covers` 不在 class 的 javadoc 裡(方法 javadoc / 行註解不算落點)")

    # ── 第三段:打在哪個入口 ────────────────────────────────────────────
    print("\n--- 第三段:打在哪個入口(**第 4 階,人讀**;只列 token,不判斷)---")
    if not files:
        print("  (沒有測試檔)")
    for tf in files:
        print(f"  · {tf.rel}  @covers:{_fmt(tf.covers)}"
              + (f"  舊約定方法 {len(tf.old_convention)} 條" if tf.old_convention else ""))
        calls = "、".join(f"{t}.{'/'.join(ms)}" for t, ms in sorted(tf.calls.items()))
        print(f"      Type.method(:{calls or '(無)'}")
        print(f"      new Type(   :{_fmt(tf.news)}")
        print(f"      Type.class  :{_fmt(tf.class_literals)}")

    print(VACUITY_NOTE)
    print(LIMITS)
    return 1 if (rep["unlanded"] or drift or unrec or misplaced or not files) else 0


def check(db_path: Path, workdir: Path) -> dict:
    """`main()` 走的就是這一支,測試也測這一支(不要再抄一份)。"""
    contracts, scenarios = load_ids(db_path)
    return judge(contracts, scenarios, scan_inner_tests(workdir), workdir)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    db_path, workdir = Path(argv[1]), Path(argv[2])
    if not db_path.is_file():
        print(f"找不到 store:{db_path}(先跑 spec_store.py import)", file=sys.stderr)
        return 2
    if not workdir.is_dir():
        # 2 不是 3:「目錄根本不在」是這支沒跑起來,不是「沒有內圈測試」。
        print(f"找不到工作目錄:{workdir} —— 這支要吃 run_act4.sh 的工作目錄", file=sys.stderr)
        return 2
    try:
        rep = check(db_path, workdir)
    except sqlite3.DatabaseError as exc:
        print(f"store 讀不出來:{db_path}({exc})", file=sys.stderr)
        return 2
    return report(rep)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
