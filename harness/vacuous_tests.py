#!/usr/bin/env python3
"""從 PIT 的 mutation matrix 產生**假驗收的分診佇列**。

治的是第 3 階唯一沒人守的洞:**假驗收**。分層實驗量到過一次
(REPORT.md:「HL1/HL2 的 no-setter 反射測試皆恆真(掃不到任何真 setter),
HL2 的 reconstruct 正好從 `set*` 字面檢查旁邊走過」)——
測試是綠的,而且**不管實作怎麼寫都會是綠的**。純綠燈擋不住這個。

⚠️ **PIT 原生答不出這個問題。** 它的輸出是「mutation score」——每個 mutant 有沒有
被殺掉。一條恆真測試不會拉低分數,因為別的測試會把 mutant 殺掉。要問「**哪條測試
什麼都沒約束到**」,得開 `fullMutationMatrix=true`(逐 mutant 記下是被哪些測試殺的)。

⚠️⚠️ **但「殺了 0 個」是錯的指標。** 這是實測出來的,不是想出來的:
拿分層實驗那條已知的恆真測試(`OrderTest.testOrderNoSetters`,只用反射看方法名)
去驗,它**殺了 7 個 mutant**,所以「零殺」偵測器回報「乾淨」——**在一個我們
知道是髒的案例上**。原因是 `@BeforeEach`:fixture 建構路徑上的 mutant 會讓
**全班每一條測試**都失敗,恆真測試因此繼承了它沒賺到的擊殺
(那 7 個全落在 `<init>` / `of()` 上,而且正好等於該類別的共同集合)。

**⚠️ 最重要的一句:mutation testing 分不出「恆真」與「碰不到」。**
兩者長得一模一樣 —— 都沒有獨佔貢獻、都只死在很多測試共用的 mutant 上。
兩個已知陽性都驗過:排名前面的全是 null 守衛與 hashCode 測試,
**那些是正當的測試,只是 PIT 表達不出它們守的東西**,而恆真測試就夾在裡面。
所以這支 script 交的是**分診佇列**:把 47 條縮到 8 條要人讀,不是替人判。
判別要靠讀那條測試在斷言什麼。

**「獨佔擊殺 = 0」也不夠好** —— 同樣是實測:它在這個樣本上標了 47 條裡的 33 條。
健康的測試本來就會互相重疊(`testAddMultipleItems` 殺了 30 個,但每一個都有別人也殺得掉),
所以「沒有獨佔」大多只代表「有人跟我一起守」,不代表恆真。訊號被雜訊淹掉了。

**「貢獻沒超出全班共同集合」在第二個已知陽性上漏抓。** 這也是實測:
HL2 那條靠 `@BeforeEach`,擊殺必然落在全班交集裡 → 抓到;
**HL1 那條在測試內自己 `new Order(...)`**,交集因此不含它殺的建構子 mutant → 漏抓。
(這個結果在跑之前就寫下了預測,理由一樣。)

**最後採用的是「被支配」:∃ 另一條測試 T′,使 kills(t) ⊆ kills(T′)。**
別人殺掉的是你的超集,代表你沒有給出任何它沒給的東西。兩個已知陽性都在裡面,
而且比「獨佔 = 0」緊(20/47 vs 33/47)。

佇列用**最小共殺數**排序:一條測試殺到的 mutant 裡,「最少人殺的那個」被幾條測試殺。
恆真測試只會死在建構路徑那種很多人都踩到的 mutant 上,所以這個數字會偏高。
兩個已知陽性分別排第 8/47 與第 5/50 —— **進得了佇列,但不會排第一**,
因為 null 守衛測試的長相跟它們一樣。

⚠️ **零殺不等於沒價值,所以這支 script 出的是候選、不是判決。**
結構型檢查(ArchUnit)、契約型檢查、只斷言「不會拋例外」的煙霧測試,本來就殺不了
行為 mutant。正確的處置是**把它們排除在 targetTests 之外**(見 build.gradle 的註解),
或列進 allowlist 並寫明理由 —— 不是把它們刪掉。

用法:
    python3 vacuous_tests.py <mutations.xml> [--allow-file <allowlist.txt>] [--allow <class.method> …]

allowlist 的每一行是 `Class.method  # 理由`,**理由是必填的** —— 少了 `#` 那一行會被拒收。
理由是這份檔案唯一的價值:一年後沒人記得為什麼某條測試被豁免,而沒有理由的豁免
會慢慢長成「全部豁免」。這跟 schema 那邊 `provenance_ref NOT NULL` 是同一招。
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

# PIT 的測試名有兩種形狀:
#   com.shop.domain.OrderTest.[engine:junit-jupiter]/[class:…]/[method:testX()]
#   com.shop.domain.OrderTest.testX(com.shop.domain.OrderTest)
CLASS_RE = re.compile(r"\[class:([^\]]+)\]")
METHOD_RE = re.compile(r"\[method:([^\(\]]+)")
PLAIN_RE = re.compile(r"^([\w.$]+)\.([\w$]+)\(")


def normalise(raw: str) -> str:
    """把 PIT 的測試識別字正規化成 Class.method。"""
    raw = raw.strip()
    if not raw:
        return ""
    cls, method = CLASS_RE.search(raw), METHOD_RE.search(raw)
    if cls and method:
        return f"{cls.group(1).rsplit('.', 1)[-1]}.{method.group(1)}"
    plain = PLAIN_RE.match(raw)
    if plain:
        return f"{plain.group(1).rsplit('.', 1)[-1]}.{plain.group(2)}"
    # 保底:留最後兩段(Class.method)。**不要只留最後一段** ——
    # 那會讓不同類別的同名測試(AT.testEquals / BT.testEquals)併成同一筆,
    # 併起來之後「獨佔擊殺」就算錯了。
    head = raw.split("/")[0]
    segments = head.rsplit(".", 2)
    return ".".join(segments[-2:]) if len(segments) >= 2 else head


def split_tests(node: ET.Element | None) -> list[str]:
    if node is None or not (node.text or "").strip():
        return []
    return [normalise(part) for part in node.text.split("|") if part.strip()]


class AllowlistError(Exception):
    pass


def load_allowlist(path: str | Path) -> set[str]:
    """讀 allowlist。每行 `Class.method  # 理由`;沒寫理由的一律拒收。"""
    allowed: set[str] = set()
    problems: list[str] = []
    for lineno, raw in enumerate(Path(path).read_text(encoding="utf-8").split("\n"), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "#" not in line:
            problems.append(f"  第 {lineno} 行沒有寫理由(格式:`Class.method  # 理由`):{line}")
            continue
        entry, reason = line.split("#", 1)
        if not entry.strip():
            problems.append(f"  第 {lineno} 行沒有測試名:{line}")
        elif not reason.strip():
            problems.append(f"  第 {lineno} 行的理由是空的:{line}")
        else:
            allowed.add(entry.strip())
    if problems:
        raise AllowlistError("allowlist 格式不合:\n" + "\n".join(problems))
    return allowed


def analyse(xml_path: str | Path) -> tuple[dict[str, dict[str, object]], int]:
    """回傳 ({測試: {kills, unique, setup_only}}, mutant 總數)。"""
    root = ET.parse(xml_path).getroot()
    killed_by: dict[str, set[int]] = {}
    seen: set[str] = set()
    total = 0
    for index, mutation in enumerate(root.iter("mutation")):
        total += 1
        killers = [t for t in split_tests(mutation.find("killingTests")) if t]
        survivors = [t for t in split_tests(mutation.find("succeedingTests")) if t]
        seen.update(killers)
        seen.update(survivors)
        for test in killers:
            killed_by.setdefault(test, set()).add(index)

    # 每個 mutant 是被幾條測試殺的 —— 只被一條殺的,那條就是它的獨佔者
    killers_per_mutant: Counter[int] = Counter()
    for mutants in killed_by.values():
        killers_per_mutant.update(mutants)

    # 同一個測試類別全員共同殺到的集合 = @BeforeEach 之類的共用路徑
    by_class: dict[str, list[str]] = {}
    for test in seen:
        by_class.setdefault(test.rsplit(".", 1)[0], []).append(test)
    common: dict[str, set[int]] = {}
    for cls, tests in by_class.items():
        sets = [killed_by.get(t, set()) for t in tests]
        common[cls] = set.intersection(*sets) if sets and all(sets) else set()

    report: dict[str, dict[str, object]] = {}
    for test in sorted(seen):
        mine = killed_by.get(test, set())
        unique = {m for m in mine if killers_per_mutant[m] == 1}
        cls = test.rsplit(".", 1)[0]
        # 被支配:別人殺掉的是我的超集 → 我沒給出任何它沒給的東西
        dominated = bool(mine) and any(
            other != test and mine <= s for other, s in killed_by.items()
        )
        report[test] = {
            "kills": len(mine),
            "unique": len(unique),
            "setup_only": bool(mine) and mine <= common.get(cls, set()),
            "dominated": dominated,
            # 殺到的 mutant 裡「最少人殺的那個」被幾條測試殺 —— 越高越可疑
            "min_cokillers": min((killers_per_mutant[m] for m in mine), default=0),
        }
    return report, total


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    allow: set[str] = set()
    if "--allow-file" in argv:
        i = argv.index("--allow-file")
        path = Path(argv[i + 1])
        if path.exists():          # 檔案不存在視為空 allowlist,不是錯誤
            try:
                allow |= load_allowlist(path)
            except AllowlistError as exc:
                print(exc, file=sys.stderr)
                return 2
        argv = argv[:i] + argv[i + 2 :]
    if "--allow" in argv:
        allow |= set(argv[argv.index("--allow") + 1 :])

    stats, total = analyse(argv[1])
    if not stats:
        print("mutation matrix 是空的 —— 確認 build.gradle 有 fullMutationMatrix=true", file=sys.stderr)
        return 2

    # 主指標是 dominated —— 兩個已知陽性都進得來。理由與另外兩個被淘汰的指標見檔頭
    flagged = sorted(
        (t for t, s in stats.items()
         if (s["dominated"] or s["kills"] == 0) and t not in allow),
        key=lambda t: -stats[t]["min_cokillers"],
    )
    print(f"mutant {total} 個,跑過的測試 {len(stats)} 條\n")
    print("獨佔擊殺最多的(這些真的在約束實作,而且無可取代):")
    for test, s in sorted(stats.items(), key=lambda kv: -kv[1]["unique"])[:5]:
        print(f"  獨佔 {s['unique']:3} / 共 {s['kills']:3}  {test}")
    print(f"\n🚩 分診佇列({len(flagged)} / {len(stats)} 條,越上面越可疑):")
    for test in flagged:
        s = stats[test]
        mark = "  ← 貢獻全來自共用 setup" if s["setup_only"] else ""
        print(
            f"  最小共殺 {s['min_cokillers']:3}  殺 {s['kills']:3}  獨佔 {s['unique']:3}"
            f"  {test}{mark}"
        )
    if allow:
        print(f"\n(allowlist 排除了 {len(allow)} 條:{sorted(allow)})")
    if flagged:
        print(
            "\n⚠️ **這是佇列,不是判決。** mutation testing 分不出下面 (a) 與 (c)"
            "\n   —— 它們在資料上長得一模一樣,要靠讀那條測試在斷言什麼:"
            "\n   (a) 恆真 —— 不管實作怎麼寫都綠(要修或刪)"
            "\n   (b) 跟另一條測試完全重複(要合併)"
            "\n   (c) 它守的東西 mutation 碰不到(字串常數、null 守衛、結構檢查"
            "\n       —— 加進 allowlist 並寫理由)"
        )
    return 1 if flagged else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
