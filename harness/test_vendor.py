"""vendor.sh 的測試 —— 「搬」是機械步驟,所以它的合約要釘住(票 32、ADR 0010)。

釘的東西:
  - 搬進乾淨的 tmp hub:exit 0、ORIGIN.md 有上游 HEAD 的 sha 和 pytest 那行、
    副本跟上游 `diff -r` 只差 ORIGIN.md
  - 再搬一次同一個 hub:exit 1、訊息有「已存在」、ORIGIN.md 一個 byte 都沒動
  - 用法錯誤(沒給參數、目錄不存在):exit 2
  - 上游樹髒:拒絕(exit 1);VENDOR_ALLOW_DIRTY=1 照搬

遞迴防線:vendor.sh 在副本裡跑 pytest,副本裡也有這個檔 —— 它會再搬一次、再跑一次
pytest……無限下去。vendor.sh 跑副本 pytest 時帶 VENDOR_INNER=1,這裡看到就整個模組 skip
(這也是為什麼副本的 pytest 結果會少一條 / 多一個 skipped)。

完整的 vendor(含副本 pytest,約 10 秒)整個模組只跑一次(module-scoped fixture),
「已存在」那條在 copy 之前就被擋掉、用法錯誤不碰 copy、髒樹那條用 tmp 裡的假 repo,
副本只有一條測試 —— 所以總共只有一次真正的 ~10 秒。

fixture 一律帶 VENDOR_ALLOW_DIRTY=1:上游 harness/ 正在開發時樹本來就是髒的,測試不能
要求先 commit。髒樹拒絕那條路有自己的假 repo 測。
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

if os.environ.get("VENDOR_INNER"):
    pytest.skip("VENDOR_INNER=1:在 vendor 出來的副本裡,不再往下搬(遞迴防線)",
                allow_module_level=True)

HARNESS = Path(__file__).resolve().parent
UPSTREAM = HARNESS.parent
VENDOR = HARNESS / "vendor.sh"


def _run(*args: str, env_extra: dict[str, str] | None = None,
         script: Path = VENDOR) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "VENDOR_ALLOW_DIRTY": "1", **(env_extra or {})}
    env.pop("VENDOR_INNER", None)
    return subprocess.run(["bash", str(script), *args], capture_output=True,
                          text=True, env=env)


def _head_sha(repo: Path) -> str:
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture(scope="module")
def vendored(tmp_path_factory: pytest.TempPathFactory):
    """整個模組唯一一次完整的 vendor。不在這裡 assert —— 副本 pytest 紅的時候,
    只讓 exit-0 那條紅,ORIGIN.md / diff 那幾條照常查得到。"""
    hub = tmp_path_factory.mktemp("hub")
    proc = _run(str(hub))
    return proc, hub


# ---- 第一次搬 -------------------------------------------------------------------

def test_搬進乾淨hub_exit0_而且印出三行(vendored):
    proc, hub = vendored
    assert proc.returncode == 0, proc.stdout + proc.stderr
    lines = proc.stdout.strip().splitlines()
    assert any(l.startswith("搬到:") for l in lines), proc.stdout
    assert any(l.startswith("來源 commit:") for l in lines), proc.stdout
    assert any(l.startswith("副本 pytest:") for l in lines), proc.stdout


def test_ORIGIN有上游HEAD的sha和pytest那行(vendored):
    _, hub = vendored
    origin = hub / "harness" / "ORIGIN.md"
    assert origin.is_file()
    text = origin.read_text(encoding="utf-8")
    assert text.startswith("# ORIGIN —— 這份 harness 從哪來")
    assert _head_sha(UPSTREAM) in text
    assert "pytest" in text
    assert len(text.splitlines()) <= 25, text


def test_副本跟上游只差ORIGIN(vendored):
    _, hub = vendored
    proc = subprocess.run(
        ["diff", "-rq", "--exclude=__pycache__", "--exclude=.pytest_cache",
         "--exclude=ORIGIN.md", str(HARNESS), str(hub / "harness")],
        capture_output=True, text=True)
    assert proc.returncode == 0 and proc.stdout == "", proc.stdout + proc.stderr


def test_副本沒留下pycache(vendored):
    _, hub = vendored
    assert not list((hub / "harness").rglob("__pycache__"))
    assert not list((hub / "harness").rglob(".pytest_cache"))


# ---- 再搬一次:不覆蓋 -----------------------------------------------------------

def test_已存在就拒絕_ORIGIN一個byte都不動(vendored):
    _, hub = vendored
    origin = hub / "harness" / "ORIGIN.md"
    before = origin.read_bytes()
    proc = _run(str(hub))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "已存在" in proc.stdout + proc.stderr
    assert origin.read_bytes() == before


# ---- 用法錯誤 -------------------------------------------------------------------

def test_沒給參數_exit2():
    proc = _run()
    assert proc.returncode == 2
    assert "用法" in proc.stderr


def test_目錄不存在_exit2(tmp_path: Path):
    proc = _run(str(tmp_path / "沒有這個目錄"))
    assert proc.returncode == 2
    assert "用法" in proc.stderr


# ---- 髒樹:拒絕;VENDOR_ALLOW_DIRTY=1 照搬 ------------------------------------------
# 不敢弄髒真的上游樹(其他人正在改),所以在 tmp 裡造一個迷你 repo:
# harness/ 只放 vendor.sh 本尊 + 一條會過的測試,commit 之後再改一個檔讓它髒。
# 這個假 repo 沒有 origin remote,順便驗「沒 remote 也搬得動」。

@pytest.fixture
def fake_upstream(tmp_path: Path) -> Path:
    repo = tmp_path / "upstream"
    (repo / "harness").mkdir(parents=True)
    shutil.copy(VENDOR, repo / "harness" / "vendor.sh")
    (repo / "harness" / "test_ok.py").write_text("def test_ok():\n    pass\n")
    git = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-q", "-m", "init"], check=True)
    (repo / "harness" / "test_ok.py").write_text("def test_ok():\n    assert True\n")
    assert subprocess.run(["git", "-C", str(repo), "status", "--porcelain"],
                          capture_output=True, text=True).stdout.strip()
    return repo


def test_髒樹拒絕(fake_upstream: Path, tmp_path: Path):
    hub = tmp_path / "hub"
    hub.mkdir()
    proc = _run(str(hub), env_extra={"VENDOR_ALLOW_DIRTY": "0"},
                script=fake_upstream / "harness" / "vendor.sh")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "髒" in proc.stderr
    assert not (hub / "harness").exists()


def test_髒樹_ALLOW_DIRTY照搬_沒remote也行(fake_upstream: Path, tmp_path: Path):
    hub = tmp_path / "hub"
    hub.mkdir()
    proc = _run(str(hub), script=fake_upstream / "harness" / "vendor.sh")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    text = (hub / "harness" / "ORIGIN.md").read_text(encoding="utf-8")
    assert _head_sha(fake_upstream) in text
    assert "沒有 origin remote" in text
    assert "1 passed" in text
