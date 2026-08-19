#!/usr/bin/env python3
"""答案落點檢查 —— 第 N 輪問出去的題,有沒有出現在第 N+1 輪開頭那張落點表裡?

第一幕唯一的機械檢查是 `relay_ledger.verify`,它只問**「答案有沒有被轉交」**。
轉交之後那個答案有沒有被**記下來**,它一概不看。而「每個答案都指得出落點」這條
判準是存在的 —— 寫在 `interview-prompt.md` §11,只是:

  1. **只在收尾時查一次**,那時漏接的那一輪早就滑過去了;
  2. **是 agent 自己查自己** —— 漏了的東西不會出現在它自己列的表裡。

中途唯一的記錄是**落點表**(每輪開頭貼的那張「他說的原話 / 我記成什麼 / 來源標記」),
它是散文、在訊息裡,**沒有任何東西在讀它**。這支就是那個讀它的東西。

判準**刻意寫笨**(寫成「大致上都有記到」這支就白做了):

    第 N 輪問出去的每一個題號,要出現在 `r(N+1)-questions.md` **開頭那張落點表**
    的某一列裡。

三個字面上的收窄全是故意的:

  * **落點表 = markdown 表格的資料列**,而且在該輪**提出新問題之前**。
    散文寫一句「收到了 Q8 到 Q11 的回答」**不算** —— 那句話裡的 Q9、Q10 根本沒出現,
    而真實語料就是這樣滑過去的。
  * **只看下一輪。** 隔一輪才補記的算漏接。
  * 明確答「沒有」「還沒想過」的**也算落點** —— 只要題號進了表就通過。
    (它們該進 §4 或未答追蹤,不是消失。)

⚠️ **已知上限:題號出現 ≠ 記對了。** 這支抓得到「**整題消失**」,
**抓不到「記成別的意思」**。後者是另一個檢查,不混進來當賣點。上限也印在報表裡。

⚠️ **最後一輪沒有下一輪 = 不適用,不是通過**(ADR 0005 §6)。報表把它印在最上面。

⚠️ **一題都沒認出來 = 不適用,不是通過**(2026-08-18 稽核 §二.A 補上)。
原本的守衛只擋「沒有成對的 rN/rN+1 檔」,擋不住「檔案成對、而題號一個都沒認出來」——
那一輪照樣算 `compared`、`asked = 0`、漏接 0,**整份綠燈**。實測:把一份 15 題的真實
run 只把題號寫法 `**Q1.` 改成 `**Q1:`(其他一字不動),報表就印「可比對 3 輪 / 0 題;
通過 0、漏接 0」而 exit 0。**訪談者換個標點,守衛靜靜地不再適用。**

離開碼:
    0  可比對的輪都通過了
    1  有漏接,或有「掃到卻掃錯」的異常(題號一輪都沒認出來 / 題號寫法漂了 / 輪次斷號)
    2  用法錯誤(吃錯目錄)
    3  **整份不適用** —— 一輪都比對不了。不是通過。

用法:
    python3 landing_check.py <run_dir> [SPEC-draft.md]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# 「這一輪問出去的題」= 粗體題號開頭的那幾行。
# 四份真實語料三種寫法都吃得下:`**Q1.**`、`**Q1. 一張訂單…**`、`**Q11.**(第二輪欠的)`。
# 刻意**不**認 `[Q7]` 這種引用形式 —— 那是「提到」不是「問出去」。
ASKED = re.compile(r"\*\*Q(\d+)\s*[.．]")

# 「差一點就認出來」的形狀:**粗體題號,但後面不是句點**(`**Q1:`、`**Q1)`、`**Q1 `)。
# 這支的判準卡在一個**標點**上,而標點是訪談者的行文習慣 —— 換一個,整份就靜靜地
# 變成 0 題。所以認得出來的近似寫法要**當場吵**,不能只在計數上少掉。
# 刻意仍然要求**粗體**:`[Q7]` / 散文裡的 `Q7` 不算(那是「提到」不是「問出去」)。
ASKED_LOOSE = re.compile(r"\*\*Q(\d+)(?![0-9])")

# 落點表的邊界:該輪開始問新問題的那一刻。之前是落點,之後是提問。
# (haiku smoke 那份的 `盤點` 表在問題**之後** —— 那不是落點表,不能算。)
FIRST_QUESTION = ASKED

# markdown 表格的資料列:`| a | b | c |`。分隔列 `|---|---|` 不算資料。
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
TABLE_SEP = re.compile(r"^\s*\|[\s:|-]+\|\s*$")

ROUND_FILE = re.compile(r"^r(\d+)-questions\.md$")


def _qn(n: int) -> re.Pattern[str]:
    """題號的比對要卡邊界 —— `Q1` **不准**被 `Q11` 滿足。

    現有語料驗不到這個 bug(opus 的 Q1 和 Q11 都有落點),但它是這種檢查
    最容易寫出來的錯,而且錯的方向是**假通過**。用合成測試釘住。
    """
    return re.compile(rf"(?<![0-9A-Za-z])Q0*{n}(?![0-9A-Za-z])")


def round_questions(run_dir: Path) -> dict[int, Path]:
    """`rounds/` 底下的逐輪提問檔,依輪次**數字**排(不是字典序 —— r10 < r2 的坑)。"""
    rounds = run_dir / "rounds"
    if not rounds.is_dir():
        raise SystemExit(f"找不到 {rounds} —— 這支要吃 orchestrate.py 的逐輪產物")
    out: dict[int, Path] = {}
    for p in rounds.iterdir():
        m = ROUND_FILE.match(p.name)
        if m:
            out[int(m.group(1))] = p
    return dict(sorted(out.items()))


def asked(text: str) -> list[int]:
    """這一輪問出去的題號,去重、保留出現順序。"""
    seen: list[int] = []
    for m in ASKED.finditer(text):
        n = int(m.group(1))
        if n not in seen:
            seen.append(n)
    return seen


def near_misses(text: str) -> list[int]:
    """粗體題號**在同一個位置**沒被 `ASKED` 認出來的那幾個 —— 「掃到卻掃錯」。

    比位置不比集合:同一輪裡 `**Q1.` 與 `**Q1:` 併存時,集合相減會把後者吃掉。
    """
    strict_starts = {m.start() for m in ASKED.finditer(text)}
    out: list[int] = []
    for m in ASKED_LOOSE.finditer(text):
        if m.start() in strict_starts:
            continue
        n = int(m.group(1))
        if n not in out:
            out.append(n)
    return out


def landing_rows(text: str) -> list[str]:
    """下一輪**開頭那張落點表**的資料列。

    「開頭」的定義是機械的:檔案開始到**第一個粗體題號**為止。之後的表格
    (盤點、未答追蹤)不是落點表 —— 它們記的是尚未落地的東西,把它們算進來
    就等於承認「我打算之後再處理」也是落點,那這支就白做了。
    """
    m = FIRST_QUESTION.search(text)
    head = text[: m.start()] if m else text
    return [
        line for line in head.splitlines()
        if TABLE_ROW.match(line) and not TABLE_SEP.match(line)
    ]


def check(run_dir: Path) -> dict:
    """逐輪比對。回傳的每一輪都帶 `status`:compared / not_applicable。

    **不適用自成一類**,絕不折進通過(ADR 0005 §6)。不適用有三種 `na_kind`,
    它們**不是同一件事**,所以分開記:

    * `last_round` —— 最後一輪,沒有下一輪可比。**預期之內**,不影響離開碼。
    * `gap` —— 輪次斷號(有 r1、r3,沒有 r2)。這一輪比不了,而且這份 run 有洞。
    * `no_questions` —— 檔案成對,**但這一輪一題都沒認出來**。
      這是 2026-08-18 稽核抓到的靜默綠燈:原本它算 `compared`、`asked = 0`、
      漏接 0,於是「什麼都沒查」印成了「全部通過」。

    後兩種是**異常**(`anomalous`),要影響離開碼 —— 不然「掃不到東西」又變成綠燈。
    """
    files = round_questions(run_dir)
    last = max(files) if files else 0
    rounds: list[dict] = []
    for n, path in files.items():
        text = path.read_text(encoding="utf-8")
        qs = asked(text)
        near = near_misses(text)
        nxt = files.get(n + 1)
        base = {"round": n, "asked": qs, "near_miss": near}
        if nxt is None:
            gap = n != last
            rounds.append({
                **base, "landed": [], "missing": [],
                "status": "not_applicable",
                "na_kind": "gap" if gap else "last_round",
                "anomalous": gap,
                "reason": (
                    f"沒有 r{n + 1}-questions.md,而 r{last}-questions.md 在 —— "
                    "**輪次斷號**,這一輪的落點表根本沒落地"
                    if gap else
                    f"沒有 r{n + 1}-questions.md(最後一輪)—— 沒有落點表可比"
                ),
                "rows": 0,
            })
            continue
        if not qs:
            # ⚠️ 這條就是靜默綠燈那條路。「一題都沒認出來」不是「沒有漏接」。
            rounds.append({
                **base, "landed": [], "missing": [],
                "status": "not_applicable",
                "na_kind": "no_questions",
                "anomalous": True,
                "reason": (
                    f"r{n}-questions.md 裡**一個題號都沒認出來**"
                    f"(判準只認 `**Qn.`)—— 沒東西可比,不是沒有漏接"
                    + (f";看到 {len(near)} 個差一點的寫法:{_fmt(near)}" if near else "")
                ),
                "rows": 0,
            })
            continue
        rows = landing_rows(nxt.read_text(encoding="utf-8"))
        blob = "\n".join(rows)
        landed = [q for q in qs if _qn(q).search(blob)]
        rounds.append({
            **base, "landed": landed,
            "missing": [q for q in qs if q not in landed],
            "status": "compared",
            "na_kind": "",
            "anomalous": bool(near),
            "reason": "" if rows else f"r{n + 1}-questions.md 開頭**沒有任何落點表**",
            "rows": len(rows),
        })
    compared = [r for r in rounds if r["status"] == "compared"]
    na = [r for r in rounds if r["status"] == "not_applicable"]
    return {
        "run": run_dir.name,
        "rounds": rounds,
        "comparable_rounds": len(compared),
        "asked_total": sum(len(r["asked"]) for r in compared),
        "landed_total": sum(len(r["landed"]) for r in compared),
        "missing_total": sum(len(r["missing"]) for r in compared),
        "na_total": sum(len(r["asked"]) for r in na),
        # ⚠️ `na_total` 數的是**題數**,而「一題都沒認出來」那種不適用的題數是 0 ——
        #    它在題數上完全隱形。所以另外數**輪數**,不然報表又會看起來乾淨。
        "na_rounds": len(na),
        "anomalies": [r for r in rounds if r["anomalous"]],
        "near_miss_total": sum(len(r["near_miss"]) for r in rounds),
    }


# ── §11 收尾表:參考,不進判定 ────────────────────────────────────────────

SPEC_LOG = re.compile(r"^#{1,4}\s*§?\s*11\b.*$", re.M)


def spec_log_questions(spec_text: str) -> list[int]:
    """`SPEC-draft.md` §11 那張逐題落點表提到的題號。

    **這張表是訪談者自己寫的** —— 漏了的東西不會出現在它自己列的表裡,
    所以它不進判定、不進計數、不影響 exit code。只印成參考。
    """
    m = SPEC_LOG.search(spec_text)
    if not m:
        return []
    tail = spec_text[m.end():]
    nxt = re.search(r"^#{1,4}\s", tail, re.M)
    section = tail[: nxt.start()] if nxt else tail
    rows = [
        line for line in section.splitlines()
        if TABLE_ROW.match(line) and not TABLE_SEP.match(line)
    ]
    seen: list[int] = []
    for n in (int(x) for x in re.findall(r"(?<![0-9A-Za-z])Q(\d+)(?![0-9A-Za-z])", "\n".join(rows))):
        if n not in seen:
            seen.append(n)
    return sorted(seen)


LIMITS = """
--- 這支檢查的上限(讀結論之前先看)---
* ⚠️ **題號出現 ≠ 記對了。** 這支抓得到「**整題消失**」,**抓不到「記成別的意思」**。
  一題被記反了、單位記錯了、候選被當成定案 —— 它一律放行。那是另一個檢查。
* **只看下一輪。** 落點寫在散文裡、或隔一輪才補記,這支都記成漏接 —— 這是**假陽性
  的方向**,標出來的要人去讀那一輪確認。
* **整題沒答、只進「未答追蹤」**而沒進落點表的,也記成漏接。
* **最後一輪是「不適用」,不是「通過」** —— 沒有下一輪就沒有落點表可比。
* **題號一題都沒認出來是「不適用」,不是「通過」** —— 判準只認 `**Qn.`(粗體 + 句點)。
  換一種寫法就掃不到,而掃不到**不算查過**。
* ⚠️ **關不掉的那一半:題號連粗體都不用的漂移,這支看不見。** 近似寫法只認得出
  **粗體**的 `**Qn`(冒號、括號、空白結尾都吵得出來);訪談者要是寫成 `Q1:` 或
  `1. …`,這支既認不出題號、也吵不出近似 —— 那一輪會落進「不適用」(不會假綠燈),
  但報表**分不出「真的沒問一題」與「寫法完全不同」**。
* **同一輪裡混用寫法時,近似只按位置報一次**:`**Q1.` 與 `**Q1:` 併存,後者吵得出來,
  但報表不會告訴你那是「同一題的兩種寫法」還是「兩題」。"""


def _fmt(qs: list[int]) -> str:
    return "、".join(f"Q{q}" for q in qs) if qs else "(無)"


def main(argv: list[str]) -> int:
    if not 2 <= len(argv) <= 3:
        print(__doc__, file=sys.stderr)
        return 2
    run_dir = Path(argv[1])
    rep = check(run_dir)

    print(f"\n=== 答案落點檢查:{rep['run']} ===")
    print("判準:第 N 輪的每個題號,要出現在 r(N+1)-questions.md 開頭那張落點表的某一列裡。\n")

    # ── 不適用印在最上面,自成一類(ADR 0005 §6)───────────────────────
    na = [r for r in rep["rounds"] if r["status"] == "not_applicable"]
    print("【不適用】—— 不是通過,沒有被檢查過")
    if na:
        for r in na:
            mark = "❌" if r["anomalous"] else "◻"
            print(f"  {mark} 第 {r['round']} 輪:{len(r['asked'])} 題({_fmt(r['asked'])})"
                  f" → {r['reason']}")
    else:
        print("  (無)")

    # ── 「掃到卻掃錯」:題號寫法漂了 ───────────────────────────────────────
    drifted = [r for r in rep["rounds"] if r["near_miss"]]
    if drifted:
        print(f"\n【題號寫法可能漂了】—— 粗體題號但判準認不出來的:"
              f"**{rep['near_miss_total']} 個**")
        for r in drifted:
            print(f"  ⚠️ 第 {r['round']} 輪:{_fmt(r['near_miss'])}"
                  f"  —— 判準只認 `**Qn.`(粗體 + 句點)")
        print("     這不是「沒問題」,是**這支檢查在這份語料上不再適用** ——"
              "認不出來的題號一律不會被查。")

    if rep["comparable_rounds"] == 0:
        # 「找不到東西所以沒問題」是最廉價的假綠燈。
        print("\n  ❌ **可比對的輪數 = 0 —— 這不是乾淨,是這份 run 沒東西可查。**")
        if not rep["rounds"]:
            print(f"     {run_dir}/rounds/ 底下一個 rN-questions.md 都沒有"
                  "(只有答案檔的舊 run 就會長這樣)。")
        elif any(r["na_kind"] == "no_questions" for r in rep["rounds"]):
            print(f"     提問檔在({rep['na_rounds']} 輪),**但一個題號都沒認出來** ——"
                  "判準只認 `**Qn.`(粗體 + 句點),題號寫法漂掉就整份掃不到。")
        else:
            print(f"     {run_dir}/rounds/ 底下沒有成對的 rN / rN+1 提問檔。")
        print("\n     **整份不適用,不是通過**(ADR 0005 §6)—— 離開碼 3,"
              "跟「有漏接」(1)分得開。")
        print(LIMITS)
        return 3

    print(f"\n【漏接】—— 問出去了,下一輪的落點表裡找不到:**{rep['missing_total']} 題**")
    if rep["missing_total"]:
        for r in rep["rounds"]:
            if r["status"] == "compared" and r["missing"]:
                note = f" —— {r['reason']}" if r["reason"] else ""
                print(f"  ⚠️ 第 {r['round']} 輪:{_fmt(r['missing'])}{note}")
                print(f"      → 讀 rounds/r{r['round'] + 1}-questions.md 的開頭,"
                      f"該處落點表共 {r['rows']} 列")
    else:
        print("  (無)")

    print(f"\n【通過】—— 題號確實出現在下一輪的落點表裡:**{rep['landed_total']} 題**")
    for r in rep["rounds"]:
        if r["status"] == "compared":
            print(f"  · 第 {r['round']} 輪:{len(r['landed'])}/{len(r['asked'])}"
                  f"  {_fmt(r['landed'])}")

    print(f"\n小計:可比對 {rep['comparable_rounds']} 輪 / {rep['asked_total']} 題;"
          f"通過 {rep['landed_total']}、漏接 {rep['missing_total']};"
          f"另有 {rep['na_total']} 題不適用(未檢查),涵蓋 {rep['na_rounds']} 輪。")
    # ⚠️ 這一句只講**不適用**那幾輪。`anomalies` 還裝著「比對過了、但同一輪另有
    #    認不出來的寫法」的 compared 輪 —— 把它們也算進「其中 N 輪是異常的不適用」,
    #    就是又寫了一次假理由(那正是本次要修的 §三.2 的病)。它們印在上面的
    #    【題號寫法可能漂了】,離開碼那邊照樣算進去。
    na_anomalous = [r for r in rep["anomalies"] if r["status"] == "not_applicable"]
    if na_anomalous:
        print(f"  ⚠️ 其中 {len(na_anomalous)} 輪是**異常的不適用**"
              f"(第 {'、'.join(str(r['round']) for r in na_anomalous)} 輪)——"
              "不是設計上比不了,是這支檢查在那幾輪上沒能適用。離開碼因此非 0。")

    if len(argv) == 3:
        spec = Path(argv[2])
        qs = spec_log_questions(spec.read_text(encoding="utf-8"))
        print(f"\n【參考,不進判定】{spec.name} §11 收尾落點表提到 {len(qs)} 個題號:{_fmt(qs)}")
        print("  ⚠️ 這張表是**訪談者自己寫的** —— 漏了的東西不會出現在它自己列的表裡。")
        print("  它**不能**把上面「不適用」的那幾輪補成「通過」,不進計數、不影響 exit code。")

    print(LIMITS)
    # 「有漏接」與「掃到卻掃錯」都是 1(要人去看);「整份比不了」是 3,上面已經回了。
    return 1 if (rep["missing_total"] or rep["anomalies"]) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
