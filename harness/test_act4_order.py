#!/usr/bin/env python3
"""`act4_order_check` 的測試 —— 用 tmp dir 模擬三態;不碰 gradle、不呼叫 claude。

預測寫在 `.scratch/ddd-harness/24-PREDICTION.md` P4,**commit 在寫程式之前**。
釘的重點不是「通過會通過」,是三條容易被折掉的邊:

- 沒有歷史是 **3 不適用**,不折成通過(票 24 明講);
- 有紀錄說做過基線、歷史卻不見了,是 **1**,不是不適用(那是異常);
- 骨架的 wiring(受保護清單裡的 `src/main` 檔)在基線裡是**對的**,不算「骨架帶了實作」。

fixture 用跟 `run_act4.sh` 一模一樣的 git 形狀:`<workdir>/harness/act4.git` 當 git-dir、
工作目錄當 work-tree —— **不放 `<workdir>/.git`**(理由見模組 docstring:gitlink)。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import act4_order_check as oc  # noqa: E402

GIT_CFG = ["-c", "user.name=h", "-c", "user.email=h@local",
           "-c", "commit.gpgsign=false", "-c", "gc.auto=0"]


def _git(work: Path, *args: str) -> str:
    return subprocess.run(
        ["git", f"--git-dir={work / oc.GIT_DIR_REL}", f"--work-tree={work}", *GIT_CFG, *args],
        capture_output=True, text=True, check=True, cwd=work,
    ).stdout


def _write(work: Path, rel: str, text: str = "x") -> None:
    p = work / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _commit_all(work: Path, msg: str) -> str:
    _git(work, "add", "-A")
    _git(work, "commit", "-q", "--allow-empty", "-m", msg)
    return _git(work, "rev-parse", "HEAD").strip()


PROTECTED = ["build.gradle",
             "src/main/java/com/shop/Application.java",
             "src/main/resources/application.properties",
             "src/test/java/acceptance/OrderAcceptanceTest.java",
             "src/test/java/acceptance/OrderProxyAcceptanceTest.java",
             "src/test/java/architecture/ArchitectureTest.java"]


def skeleton(work: Path) -> str:
    """照 runner 的順序:骨架 + 三支測試 + 受保護清單就位,再 init、commit 基線。回基線 hash。"""
    for rel in PROTECTED:
        _write(work, rel)
    _write(work, "src/main/java/com/shop/domain/.gitkeep", "")
    _write(work, oc.PROTECTED_REL, "\n".join(f"{'0' * 64}  {p}" for p in PROTECTED) + "\n")
    (work / oc.GIT_DIR_REL).parent.mkdir(parents=True, exist_ok=True)
    _git(work, "init", "-q", "--template=")
    (work / oc.GIT_DIR_REL / "info").mkdir(exist_ok=True)
    (work / oc.GIT_DIR_REL / "info" / "exclude").write_text(oc.GIT_DIR_REL + "/\n")
    base = _commit_all(work, "harness-injected baseline")
    (work / oc.META_REL).write_text(json.dumps({"baseline_commit": base}), encoding="utf-8")
    return base


# ── 通過:測試在基線裡,實作之後才來 ────────────────────────────────────

def test_實作在基線之後_通過(tmp_path: Path) -> None:
    base = skeleton(tmp_path)
    _write(tmp_path, "src/main/java/com/shop/domain/Order.java")
    _write(tmp_path, "src/innerTest/java/OrderTest.java")
    _commit_all(tmp_path, "agent output")
    code, lines = oc.check(tmp_path)
    assert code == 0, lines
    assert any("3/3 在基線裡" in l for l in lines)
    assert any("1/1 首次出現在基線之後" in l for l in lines)
    assert any(base[:12] in l and "相符" in l for l in lines)


def test_只有基線_dry_run_的形狀_通過(tmp_path: Path) -> None:
    """dry run:HEAD = 基線,`src/main` 只有受保護的 wiring 與 .gitkeep → 0 個實作檔,通過。
    這條釘的是**受保護清單的排除有接上**:`Application.java` 在基線裡不算「骨架帶了實作」。"""
    skeleton(tmp_path)
    code, lines = oc.check(tmp_path)
    assert code == 0, lines
    assert any("實作檔:0 個" in l for l in lines)
    assert any("= 基線" in l for l in lines)


# ── 1:順序壞了 ──────────────────────────────────────────────────────────

def test_骨架帶了實作_基線裡有非受保護的_src_main_檔(tmp_path: Path) -> None:
    (tmp_path / "src/main/java/com/shop/domain").mkdir(parents=True)
    _write(tmp_path, "src/main/java/com/shop/domain/Order.java")   # 基線之前就在
    skeleton(tmp_path)
    code, lines = oc.check(tmp_path)
    assert code == 1
    assert any("實作檔在基線裡" in l and "Order.java" in l for l in lines)


def test_測試檔在基線之後才出現(tmp_path: Path) -> None:
    skeleton(tmp_path)
    _write(tmp_path, "src/test/java/acceptance/SneakyTest.java")
    _commit_all(tmp_path, "agent output")
    code, lines = oc.check(tmp_path)
    assert code == 1
    assert any("測試檔不在基線裡" in l and "SneakyTest.java" in l for l in lines)


def test_src_底下沒_commit_的變更(tmp_path: Path) -> None:
    skeleton(tmp_path)
    _write(tmp_path, "src/main/java/com/shop/domain/Order.java")   # 沒 commit
    code, lines = oc.check(tmp_path)
    assert code == 1
    assert any("沒 commit 的變更" in l and "Order.java" in l for l in lines)


def test_src_以外沒_commit_的變更不算(tmp_path: Path) -> None:
    """runner 在檢查之後才落 order-check.txt,歸檔後重跑不能因為它而翻 1。"""
    skeleton(tmp_path)
    _write(tmp_path, "order-check.txt")
    _write(tmp_path, "result.json")
    code, _ = oc.check(tmp_path)
    assert code == 0


def test_run_meta_記的基線與歷史對不上(tmp_path: Path) -> None:
    skeleton(tmp_path)
    _write(tmp_path, "src/main/java/com/shop/domain/Order.java")
    _commit_all(tmp_path, "agent output")
    # 改寫歷史:把兩個 commit 壓成一個新的 root
    _git(tmp_path, "checkout", "-q", "--orphan", "rewritten")
    _commit_all(tmp_path, "rewritten")
    code, lines = oc.check(tmp_path)
    assert code == 1
    assert any("歷史被改寫過" in l for l in lines)


def test_有紀錄說做過基線_但歷史不見了_是1不是不適用(tmp_path: Path) -> None:
    skeleton(tmp_path)
    subprocess.run(["rm", "-rf", str(tmp_path / oc.GIT_DIR_REL)], check=True)
    code, lines = oc.check(tmp_path)
    assert code == 1
    assert any("歷史被拿掉了" in l for l in lines)


# ── 3:不適用,不折成通過 ────────────────────────────────────────────────

def test_沒有歷史也沒有紀錄_是3不適用(tmp_path: Path) -> None:
    """舊 run 的形狀:檔案都在,但從來沒有做過基線。**不是通過**。"""
    for rel in PROTECTED:
        _write(tmp_path, rel)
    _write(tmp_path, "src/main/java/com/shop/domain/Order.java")
    code, lines = oc.check(tmp_path)
    assert code == 3
    assert lines[0].startswith("【不適用】")


def test_不適用的工作目錄就算住在別的_git_repo_底下也是3(tmp_path: Path) -> None:
    """票 24 的坑:工作目錄住在主 repo 裡,靠 discovery 會查到主 repo 而永遠不響。
    這裡把工作目錄放進一個外層 repo,本檢查仍要回 3。"""
    outer = tmp_path / "outer"
    work = outer / "runs" / "x"
    work.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(outer)], check=True)
    _write(work, "src/test/java/T.java")
    code, _ = oc.check(work)
    assert code == 3


def test_有_git_dir_但零_commit_是3(tmp_path: Path) -> None:
    (tmp_path / oc.GIT_DIR_REL).parent.mkdir(parents=True)
    _git(tmp_path, "init", "-q", "--template=")
    code, lines = oc.check(tmp_path)
    assert code == 3
    assert lines[0].startswith("【不適用】")


# ── 2:用法錯誤 ─────────────────────────────────────────────────────────

def test_吃錯目錄是2(tmp_path: Path) -> None:
    assert oc.main(["act4_order_check.py", str(tmp_path / "nope")]) == 2


def test_沒給參數是2() -> None:
    assert oc.main(["act4_order_check.py"]) == 2


# ── 報表上限要印出來(票 24 第 4 點)────────────────────────────────────

def test_報表印上限(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    skeleton(tmp_path)
    assert oc.main(["act4_order_check.py", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "查得出,擋不住" in out
    assert "commit --amend" in out
