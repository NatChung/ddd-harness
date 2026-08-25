#!/usr/bin/env python3
"""幕四順序檢查 —— 測試是不是在實作之前就在?

`run_act4.sh` 的雜湊基線(`tamper-check.txt`)只證明「受保護檔沒被動」;
「測試先於實作存在」那條今天靠幕三 → 幕四的**構造順序**保證,沒有機械檢查
(票 24;`PIPELINE.md` 幕四「⚠️ 結構隔離不是防竄改」那段)。

⚠️ **直接抄 ai-harness-template 的 `check-test-first.sh` 會抄到一支永遠不會響的檢查**:
   幕四工作目錄是 bare dir,不是 git repo;跑完的產物被一次 commit 進主 repo 的 run 目錄,
   「測試首次 commit 早於 source 首次 commit」在那裡退化成**同一個 commit**,永遠相等。
   所以形狀改成:**工作目錄自己要有一份 git 歷史**(`harness/act4.git`,由 runner 在
   注入完、呼叫 claude 之前 `git init` + commit 一版基線;跑完再 commit 一版),
   本檢查看的是「每個檔第一次出現在基線裡,還是基線之後」。

⚠️ **歷史不放 `<workdir>/.git`,放 `<workdir>/harness/act4.git`**(`--git-dir` / `--work-tree`
   分離)。git 2.54 實測:工作目錄底下有 `.git`,外層 `git add` 會把整個 run 目錄記成
   gitlink(mode 160000),run 的檔案一個都進不了主 repo —— 而 run 目錄正是要 commit 進主 repo
   當證據的。放 `harness/act4.git` 外層 repo 把它當普通檔案收。
   代價:agent 自己 `git commit` 不會進這份歷史(它看不到那是 git dir);跑完那一版 commit
   是 runner 打的,所以本檢查分得出「基線裡 / 基線之後」,分不出 agent 內部的先後順序。

判準**刻意寫笨**:

    「測試檔」= HEAD 裡 `src/test/**` 每一個檔,**都必須在基線 commit 的樹裡**;
    「實作檔」= HEAD 裡 `src/main/**` 扣掉受保護清單與 `.gitkeep`,**都不得在基線的樹裡**。

受保護清單從**基線 commit** 讀(`harness/protected-baseline.txt`,runner 在基線之前就寫好),
不讀工作樹 —— 對已歸檔的 run 結果決定性,也少一個 agent 可寫的洞。骨架的 wiring
(`Application.java`、`application.properties`)在受保護清單裡,所以「在基線裡」是對的;
清單之外的 `src/main` 檔在基線裡 = **骨架帶了實作**,那是骨架的問題,點名印出來。
被刪掉的測試檔本檢查不管 —— 那是 `tamper-check.txt` 的事。

三態(ADR 0005 §6、`CONTEXT.md`〈不適用〉):

    0  測試檔全在基線裡,實作檔全在基線之後
    1  任一測試檔不在基線 / 任一實作檔在基線裡 / 測試檔一支都沒有 /
       `src/` 底下有沒 commit 的變更(順序查不到它們)/ root commit 不只一個 /
       `run-meta.json` 記的基線與歷史對不上 / **有紀錄說做過基線但歷史不見了**
    2  用法錯誤(吃錯目錄)
    3  **不適用 —— 工作目錄沒有 git 歷史,也沒有任何做過基線的紀錄(舊 run)。不折成通過。**

⚠️ 上限(印在報表裡,不要只寫在這裡):跟雜湊一樣是「查得出,擋不住」。agent 在
   `harness/act4.git` 上 `commit --amend`、改寫歷史、或連 `run-meta.json` 一起刪掉,
   本檢查就過。基線 commit 的 hash 另外寫在 `run-meta.json`,事後能比。

用法:
    python3 act4_order_check.py <workdir>
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

GIT_DIR_REL = "harness/act4.git"
PROTECTED_REL = "harness/protected-baseline.txt"
META_REL = "run-meta.json"
TEST_PREFIX = "src/test/"
IMPL_PREFIX = "src/main/"

EXIT_OK, EXIT_FAIL, EXIT_USAGE, EXIT_NA = 0, 1, 2, 3


class UsageError(Exception):
    pass


def git(workdir: Path, *args: str) -> str:
    """對工作目錄自己那份歷史下指令 —— 一律指明 git-dir 與 work-tree,不靠 discovery。

    工作目錄常常就住在主 repo 底下;靠 discovery 會查到主 repo,那正是票 24 說的
    「永遠不會響」的那條路。
    """
    out = subprocess.run(
        ["git", f"--git-dir={workdir / GIT_DIR_REL}", f"--work-tree={workdir}", *args],
        capture_output=True, text=True, check=True,
    )
    return out.stdout


def recorded_baseline(workdir: Path) -> str | None:
    """`run-meta.json` 記的基線 hash;沒有檔、沒有欄位、壞 JSON 都回 None。"""
    meta = workdir / META_REL
    if not meta.is_file():
        return None
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    value = data.get("baseline_commit") if isinstance(data, dict) else None
    return value if isinstance(value, str) and value else None


def protected_paths(workdir: Path, baseline: str) -> set[str]:
    """基線 commit 裡的受保護清單(`sha  path` / `MISSING  path` 一列一個)。"""
    try:
        text = git(workdir, "show", f"{baseline}:{PROTECTED_REL}")
    except subprocess.CalledProcessError:
        return set()
    paths: set[str] = set()
    for line in text.splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2:
            paths.add(parts[1].strip())
    return paths


def check(workdir: Path) -> tuple[int, list[str]]:
    """回 (離開碼, 報表列)。報表列已經照「不適用印最上面」排好。"""
    if not workdir.is_dir():
        raise UsageError(f"不是目錄:{workdir}")

    lines: list[str] = []
    recorded = recorded_baseline(workdir)
    gitdir = workdir / GIT_DIR_REL

    # ── 不適用印在最上面,自成一類(ADR 0005 §6)────────────────────────
    if not gitdir.is_dir():
        if recorded:
            lines.append("❌ run-meta.json 記著基線 commit "
                         f"{recorded[:12]},但 {GIT_DIR_REL} 不在 —— 歷史被拿掉了,這不是不適用")
            return EXIT_FAIL, lines
        lines.append("【不適用】—— 不是通過,這個工作目錄這次沒有被檢查過")
        lines.append(f"  沒有 {GIT_DIR_REL},也沒有 run-meta.json 記過基線:"
                     "這一跑沒有做過「注入後先 commit 基線」那步(舊 run,或 runner 沒跑到那裡)")
        lines.append("  **整份不適用,不是通過**(ADR 0005 §6)—— 離開碼 3,跟「吃錯目錄」(2)分得開。")
        return EXIT_NA, lines

    try:
        roots = git(workdir, "rev-list", "--max-parents=0", "HEAD").split()
    except subprocess.CalledProcessError:
        if recorded:
            lines.append(f"❌ run-meta.json 記著基線 commit {recorded[:12]},但 {GIT_DIR_REL} 裡一個 commit 都沒有")
            return EXIT_FAIL, lines
        lines.append("【不適用】—— 不是通過,這個工作目錄這次沒有被檢查過")
        lines.append(f"  {GIT_DIR_REL} 在,但一個 commit 都沒有 —— 基線沒 commit 成")
        return EXIT_NA, lines

    failures: list[str] = []
    if len(roots) != 1:
        failures.append(f"root commit 有 {len(roots)} 個({', '.join(r[:12] for r in roots)}),分不出哪個是基線")
    baseline = roots[0]
    if recorded and recorded != baseline:
        failures.append(f"run-meta.json 記的基線 {recorded[:12]} ≠ 歷史的 root commit {baseline[:12]} —— 歷史被改寫過")

    head = git(workdir, "rev-parse", "HEAD").strip()
    baseline_tree = set(git(workdir, "ls-tree", "-r", "--name-only", baseline).split("\n")) - {""}
    head_tree = set(git(workdir, "ls-tree", "-r", "--name-only", "HEAD").split("\n")) - {""}
    protected = protected_paths(workdir, baseline)

    tests = sorted(p for p in head_tree if p.startswith(TEST_PREFIX))
    impls = sorted(p for p in head_tree
                   if p.startswith(IMPL_PREFIX) and p not in protected and Path(p).name != ".gitkeep")

    if not tests:
        failures.append(f"HEAD 裡 {TEST_PREFIX}** 一個測試檔都沒有 —— 沒有東西可以「先於實作」")
    late_tests = [p for p in tests if p not in baseline_tree]
    for p in late_tests:
        failures.append(f"測試檔不在基線裡(基線之後才出現):{p}")
    early_impls = [p for p in impls if p in baseline_tree]
    for p in early_impls:
        failures.append(f"實作檔在基線裡(骨架帶了實作?那是骨架的問題):{p}")

    dirty = [l for l in git(workdir, "status", "--porcelain", "--", "src").splitlines() if l.strip()]
    for l in dirty:
        failures.append(f"src/ 底下有沒 commit 的變更,順序查不到它:{l.strip()}")

    lines.append(f"基線 commit:{baseline[:12]}" + ("(與 run-meta.json 相符)" if recorded == baseline else
                                                    "(run-meta.json 沒記)" if not recorded else ""))
    lines.append(f"HEAD:{head[:12]}" + ("(= 基線,跑完沒有第二個 commit)" if head == baseline else ""))
    lines.append(f"測試檔:{len(tests) - len(late_tests)}/{len(tests)} 在基線裡")
    wiring = sorted(p for p in protected & head_tree if p.startswith(IMPL_PREFIX))
    lines.append(f"實作檔:{len(impls)} 個(扣掉受保護的骨架 wiring {len(wiring)} 個與 .gitkeep),"
                 f"{len(impls) - len(early_impls)}/{len(impls)} 首次出現在基線之後")
    if failures:
        lines.append("")
        lines.extend(f"  ❌ {f}" for f in failures)
    return (EXIT_FAIL if failures else EXIT_OK), lines


LIMITS = """
--- 這份報表的上限(讀之前先看)---
* **查得出,擋不住** —— 跟雜湊基線同一種性質。agent 對 harness/act4.git 做
  `commit --amend`、改寫歷史、或把它連 run-meta.json 一起刪掉,本檢查就過(或回 3)。
  基線 hash 另外記在 run-meta.json,事後能比;但 run-meta.json 也在工作目錄裡。
* **「在基線裡」只證明檔案先在,不證明那條測試真的在驗什麼** —— 那是 acceptance_gwt
  與 vacuous_tests 的事。
* **agent 自己的 commit 不在這份歷史裡**(它看不到 harness/act4.git 是 git dir),
  所以只分得出「基線裡 / 基線之後」,分不出 agent 內部誰先誰後。
* 被刪掉的測試檔本檢查不管 —— 那是 tamper-check.txt 的事。"""


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return EXIT_USAGE
    workdir = Path(argv[1])
    try:
        code, lines = check(workdir)
    except UsageError as exc:
        print(exc, file=sys.stderr)
        return EXIT_USAGE
    except subprocess.CalledProcessError as exc:
        print(f"git 失敗:{exc.stderr.strip()}", file=sys.stderr)
        return EXIT_USAGE

    print(f"\n=== 幕四順序檢查:{workdir} ===")
    verdict = {EXIT_OK: "✅ 通過:測試在基線裡,實作全在基線之後",
               EXIT_FAIL: "❌ 未通過",
               EXIT_NA: "⏭️ 不適用(不是通過)"}[code]
    print(verdict + "\n")
    for line in lines:
        print(line)
    print(LIMITS)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
