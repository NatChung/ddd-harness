#!/usr/bin/env python3
"""來源標記的分診佇列 —— 宣稱出自需求方的具體值,他真的說過嗎?

訪談 prompt 的鐵律 2 是「查無來源的 = 捏造」。2026-08-18 量到它擋不住兩種東西,
**而兩種都產出合法的 `[Qn]`、都指得出行號**:

  A 需求方自己編一個凍結 SPEC 裡沒有的值(haiku:`ORD-20260818-001`、「秒級」)
  B **訪談者把值寫進誘導式提問,再標成「他親口確認的」**(opus,已 commit 的產出)

    Q9「舉例:客人昨天用 100 元買了一件,今天你們把這個商品改成 120 元…」
    需求方全文:「不會,舊的那筆單就是顯示他當時下單的價格」← 沒說過 100 或 120
    SPEC-draft:「那組數字是他在 Q9 **親口確認的**」

> **來源標記分不出「他真的說了」與「我餵給他、他沒否認」。**
> 這是「規格沉默分不出『他沒說』與『他說了但沒送到』」的同一家族。

**這支只抓 B。** A 的值確實出現在答案裡,字串比對必然放行 —— 那要靠票 04
(需求方回答 vs 凍結 SPEC),是另一個比對、另一份基準。**兩張票合起來才完整;
只跑這支就宣稱「來源都可信」是錯的。**

⚠️ **它是分診佇列,不是判決。** 最大的漏抓是單位換算與同義改寫:
答案說「一百二十元」、規格寫 `12000`,字串比對必漏。上限寫在報表裡。

用法:
    python3 provenance_check.py <run_dir> <spec.md>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# 只掃 [Qn] —— `推導自` / `本案自決` 的值本來就不該出現在答案裡
# (總額是算出來的、HTTP 形式是自決的),掃它們只會製造假陽性。
QN = re.compile(r"\[Q(\d+)\]")

# 具體值:整數(含千分位)、小數、以及帶連字號/底線的識別碼格式。
# 刻意**不抓**純英文單字與中文 —— 那些同義改寫太多,假陽性會淹掉訊號。
VALUE = re.compile(r"""
    (?<![\w.-])
    (?:
        [A-Z][A-Z0-9]*(?:[-_][A-Z0-9]+){1,}      # ORD-20260818-001 / C-001
      | \d{1,3}(?:,\d{3})+(?:\.\d+)?             # 1,500.00
      | \d+\.\d+                                  # 89.50
      | \d{2,}                                    # 100 / 12000(1 位數噪音太大)
    )
    (?![\w.-])
""", re.VERBOSE)

# 這些數字是規格的骨架不是需求方的話,掃了只會吵:HTTP 狀態碼、年份。
NOISE = {"200", "201", "400", "401", "403", "404", "500", "2026", "2025"}

# 題號不是資料值。第一版沒濾,6 筆標記裡 4 筆是 `R1-Q3` / `R3-Q13` 這種
# ——**假陽性佔 67%,那樣的佇列沒人會看**。這是訪談自己的編號體系,
# 不是需求方講的內容,濾掉是有依據的,不是為了讓數字好看。
LABEL = re.compile(r"^(?:R\d+-)?Q\d+$|^S\d+$|^C\d+$")

# 標準編號不是資料值(「ISO 8601」的 8601)。用**上下文**濾而不是把數字加進黑名單
# —— 黑名單會愈長愈像在調參數,而調到剛好讓已知陽性活著就是自欺。
STANDARD = re.compile(r"(?:ISO|RFC|UTF|HTTP|IEEE|ANSI)[\s-]*$", re.I)


def answers_corpus(run_dir: Path) -> str:
    """全部輪次的需求方回答。

    刻意合併成一份而不逐輪比對:值出現在第 2 輪、規格標 `[Q9]`(第 3 輪)是
    正常的引用,逐輪比對會把它當陽性。代價是抓不到「標錯輪次」——**選前者**,
    因為標錯輪次是查得到的小事,而假陽性會讓整個佇列沒人看。
    """
    rounds = run_dir / "rounds"
    if not rounds.is_dir():
        raise SystemExit(f"找不到答案語料:{rounds}(這支要吃 orchestrate.py 的產物)")
    parts = [p.read_text(encoding="utf-8") for p in sorted(rounds.glob("*-answers.md"))]
    if not parts:
        raise SystemExit(f"{rounds} 底下沒有 *-answers.md")
    return "\n".join(parts)


def claims(spec_text: str) -> list[tuple[int, str, str]]:
    """規格裡「這一行標了 [Qn],而且帶著具體值」的每一筆。

    回傳 (行號, 值, 該行原文)。一行有多個值就拆成多筆 —— 逐值判定,
    不要因為一行裡有一個值對得上就整行放行。
    """
    out: list[tuple[int, str, str]] = []
    for lineno, line in enumerate(spec_text.splitlines(), 1):
        if not QN.search(line):
            continue
        for m in VALUE.finditer(line):
            value = m.group(0)
            if value in NOISE or LABEL.match(value):
                continue
            if STANDARD.search(line[:m.start()]):
                continue
            out.append((lineno, value, line.strip()))
    return out


def check(run_dir: Path, spec_path: Path) -> list[dict]:
    corpus = answers_corpus(run_dir)
    # 逗號千分位在答案裡常寫成沒逗號的,兩種都認
    corpus_plain = corpus.replace(",", "")
    flagged = []
    for lineno, value, line in claims(spec_path.read_text(encoding="utf-8")):
        if value in corpus or value.replace(",", "") in corpus_plain:
            continue
        flagged.append({"line": lineno, "value": value, "text": line})
    return flagged


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    run_dir, spec_path = Path(argv[1]), Path(argv[2])
    total = len(claims(spec_path.read_text(encoding="utf-8")))
    flagged = check(run_dir, spec_path)

    print(f"\n=== 來源標記分診:{spec_path.name} ===")
    print(f"標 [Qn] 且帶具體值的:{total} 筆;**答案語料裡找不到的:{len(flagged)} 筆**\n")
    for f in flagged:
        print(f"  ⚠️ L{f['line']}  值 {f['value']!r} 沒出現在需求方的任何回答裡")
        print(f"      {f['text'][:110]}")
    if total == 0:
        # 「找不到東西所以沒問題」是最廉價的假綠燈。
        print("  ❌ 一筆都沒掃到 —— 不是乾淨,是這份規格沒有標 [Qn] 的具體值,或格式對不上")
        return 1
    print(f"""
--- 這份佇列的上限(讀之前先看)---
* **這是分診佇列,不是判決。** 標出來的要人去讀逐字稿確認。
* **抓得到**:訪談者把值寫進提問、需求方沒複述,而規格標成 [Qn](形狀 B)。
* **抓不到**:需求方自己編了一個凍結 SPEC 沒有的值(形狀 A)—— 那個值確實在
  答案裡,本檢查必然放行。**A 要靠票 04,兩張合起來才完整。**
* **抓不到**:單位換算與同義改寫(答案「一百二十元」vs 規格 `12000`)。
  這是最常見的漏抓,**零標記不等於來源都可信**。""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
