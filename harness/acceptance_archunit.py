#!/usr/bin/env python3
"""生成器的驗收:**綠 ＋ 逐條可紅**。

純綠燈證明不了任何事 —— 一條恆真的測試也是綠的(分層實驗新發現的洞層:
「恆真反射測試」)。所以驗收有兩半:

  1. 生成的 ArchitectureTest 對乾淨的骨架跑 → 全綠
  2. 逐條把規則違反掉 → **只有對應那一條**變紅,其餘仍綠

第二半才是「這條規則真的被強制了」的證據。

不動 examples/shop/app/(逐位元組凍結在 4567d31)—— 每一輪都複製到 scratch 再改。

用法:
    python3 acceptance_archunit.py <generated/ArchitectureTest.java> <workdir>
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent
SHOP_APP = REPO / "examples" / "shop" / "app"
TEST_REL = Path("src/test/java/architecture/ArchitectureTest.java")
MAIN = Path("src/main/java/com/shop")

# 每條規則一個最小違反物,加上**預期變紅的集合**。
#
# 為什麼是集合而不是「只有它」:規則之間可能互相蘊含。A6(不得掛 JPA/Jackson
# annotation)在 domain/ 上必然同時違反 A1(不得依賴框架)—— annotation 本身
# 就是一條依賴,不管有沒有寫 import。這不是 bug,是**A6 對 domain/ 被 A1 蓋住**。
# 讓預期值寫成集合,這件事才會現形而不是被「只有它紅」的斷言蓋掉。
VIOLATIONS: dict[str, tuple[list[tuple[Path, str]], set[str]]] = {
    "A1": (
        [
            (
                MAIN / "domain" / "Order.java",
                "package com.shop.domain;\n\n"
                "import org.springframework.stereotype.Component;\n\n"
                "@Component\npublic class Order {\n}\n",
            )
        ],
        {"A1"},
    ),
    "A2": (
        [
            (
                MAIN / "usecase" / "PlaceOrderUseCase.java",
                "package com.shop.usecase;\n\n"
                "import org.springframework.stereotype.Service;\n\n"
                "@Service\npublic class PlaceOrderUseCase {\n}\n",
            )
        ],
        {"A2"},
    ),
    "A3": (
        [
        (
            MAIN / "usecase" / "OrderListItem.java",
            "package com.shop.usecase;\n\npublic class OrderListItem {\n}\n",
        ),
        (
            MAIN / "domain" / "Order.java",
            "package com.shop.domain;\n\n"
            "import com.shop.usecase.OrderListItem;\n\n"
            "public class Order {\n"
            "    OrderListItem leak;\n"
            "}\n",
        ),
        ],
        {"A3"},
    ),
    "A4": (
        [
        (
            MAIN / "adapter" / "JpaOrderRepository.java",
            "package com.shop.adapter;\n\npublic class JpaOrderRepository {\n}\n",
        ),
        (
            MAIN / "usecase" / "PlaceOrderUseCase.java",
            "package com.shop.usecase;\n\n"
            "import com.shop.adapter.JpaOrderRepository;\n\n"
            "public class PlaceOrderUseCase {\n"
            "    JpaOrderRepository leak;\n"
            "}\n",
        ),
        ],
        {"A4"},
    ),
    # 刻意**只在欄位上**掛 annotation,類別本身乾淨 —— 用來證明生成的條件
    # 有查到 member,而不是只看類別層級(輪 1 實際出現的樣子就是欄位層級)。
    "A6": (
        [
            (
                MAIN / "domain" / "Order.java",
                "package com.shop.domain;\n\n"
                "public class Order {\n"
                "    @jakarta.persistence.Column(name = \"total\")\n"
                "    long totalCents;\n"
                "}\n",
            )
        ],
        {"A1", "A6"},  # 見上面的說明:A6 對 domain/ 被 A1 蓋住
    ),
    # A10 是第一個**確定不被依賴規則蓋住**的檢查:adapter 允許依賴 domain
    # (它要做對映),所以「Controller 回傳 Order」不觸發任何 dependency 規則。
    # 預期紅的只有 A10 —— 那就是「新 kind 真的增加偵測力」的證據。
    "A10": (
        [
            (
                MAIN / "domain" / "Order.java",
                "package com.shop.domain;\n\npublic class Order {\n}\n",
            ),
            (
                MAIN / "adapter" / "OrderController.java",
                "package com.shop.adapter;\n\n"
                "import com.shop.domain.Order;\n\n"
                "public class OrderController {\n"
                "    public Order get() {\n"
                "        return new Order();\n"
                "    }\n"
                "}\n",
            ),
        ],
        {"A10"},
    ),
}


def stage(generated: Path, workdir: Path, label: str) -> Path:
    """把凍結的骨架複製一份,換掉 ArchitectureTest 為生成物。"""
    target = workdir / label
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(SHOP_APP, target)
    dest = target / TEST_REL
    dest.write_text(generated.read_text(encoding="utf-8"), encoding="utf-8")
    # 骨架的驗收測試會紅(還沒實作),本驗收只跑架構那支
    (target / "src/test/java/acceptance/OrderAcceptanceTest.java").unlink()
    return target


def run_tests(app: Path) -> dict[str, str]:
    """跑架構測試,回傳 {規則 id: passed|failed}。

    注意 JUnit XML 的 testcase@name 是 @DisplayName 的字串,不是方法名
    —— 所以兩種都認,再正規化回規則 id。
    """
    proc = subprocess.run(
        [
            "./gradlew",
            "test",
            "--tests",
            "architecture.ArchitectureTest",
            "--offline",
            "--console=plain",
            "-q",
        ],
        cwd=app,
        capture_output=True,
        text=True,
    )
    results: dict[str, str] = {}
    for xml in (app / "build/test-results/test").glob("TEST-*.xml"):
        for case in ET.parse(xml).getroot().iter("testcase"):
            name = (case.get("name") or "").removesuffix("()")
            match = re.match(r"rule_(A\d+)$", name) or re.match(r"^(A\d+):", name)
            if not match:
                continue
            failed = any(child.tag in {"failure", "error"} for child in case)
            results[match.group(1)] = "failed" if failed else "passed"
    if not results:
        print(proc.stdout[-4000:], file=sys.stderr)
        print(proc.stderr[-4000:], file=sys.stderr)
        raise SystemExit(f"{app.name}:沒有測試結果,gradle 沒跑起來")
    return results


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    generated, workdir = Path(argv[1]).resolve(), Path(argv[2]).resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    rule_ids = sorted(VIOLATIONS)
    verdicts: list[tuple[str, bool, str]] = []

    # 第一半:乾淨骨架 → 全綠
    clean = run_tests(stage(generated, workdir, "clean"))
    all_green = all(v == "passed" for v in clean.values())
    missing = [r for r in rule_ids if r not in clean]
    verdicts.append(
        (
            "clean 全綠",
            all_green and not missing,
            f"{sum(v == 'passed' for v in clean.values())}/{len(clean)} 綠"
            + (f";缺 {missing}" if missing else ""),
        )
    )

    # 第二半:逐條可紅
    for rid in rule_ids:
        files, expected_red = VIOLATIONS[rid]
        app = stage(generated, workdir, f"break-{rid}")
        for rel, source in files:
            path = app / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding="utf-8")
        res = run_tests(app)
        reds = {k for k, v in res.items() if v == "failed"}
        verdicts.append(
            (
                f"{rid} 違反 → 紅的正好是 {sorted(expected_red)}",
                reds == expected_red,
                f"實際紅的是 {sorted(reds)}",
            )
        )

    print("\n=== 生成器驗收 ===")
    ok = True
    for name, passed, detail in verdicts:
        print(f"  {'✅' if passed else '❌'} {name:24} {detail}")
        ok = ok and passed
    print("=== " + ("全部通過" if ok else "有項目未通過") + " ===")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
