#!/usr/bin/env python3
"""`CLAUDE.md`〈票怎麼開、怎麼關〉的 lint —— 那段規約在票 22 之前一條都沒有東西在守。

對 `<repo_root>/.scratch/ddd-harness/`(票、預測檔)與 `examples/**/runs/`(被票引用的跑)掃,
第一批九條規則(票 22、ADR 0007):

    ticket-filename           `NN-kebab-slug.md`,NN 兩位數且不重號                 祖父 否
    status-vocabulary         第一個 `**Status:**` 的第一個詞在六個詞裡              祖父 是
    status-single-cell        只有一個 `**Status:**` 行(整格重寫,不追加)           祖父 是
    prediction-before-result  有 `X-RESULT.md` 就要有 `X-PREDICTION.md`,且不晚於它    祖父 否
    prediction-before-run     票引用的 run 目錄不早於該票的 `NN-PREDICTION.md`        祖父 是
    referenced-run-exists     票裡每個 `runs/<name>` 在 `examples/**/runs/` 找得到    祖父 否
    blocked-by-resolvable     `**Blocked by:**` 提到的票號存在                        祖父 是
    convention-undecided      ADR 0007 §4 的分診佇列(**佇列不是判決,不計入離開碼**) 祖父 是
    ticket-count-in-docs      三份文件寫的「N 張」= 實際張數                          祖父 否

形狀照 Agentheim `lib/spike-stop-loss.mjs` / `duplicate-id-check.mjs`(survey §3 第 12 條):
  - 只用 stdlib;
  - side-effect-free —— 吃一個 root,吐 `Finding` 清單,不寫任何東西;
  - loss-tolerant —— 讀不到的檔、git 不可用,**不標**(「分不出來就不標」),但印在報表上限;
  - `ADOPTION_DATE` 祖父條款:**用 git 首次 commit 日期,不用 mtime**(`touch` 就過)。

祖父怎麼判(ADR 0007 §2):檔案的 git 首次 commit 日期 **≤ ADOPTION_DATE → 祖父**,
嚴格之後才算新。⚠️ 跟 Agentheim 有一處刻意不同:**還沒 commit 的檔算新,不算「無法判定」**——
這裡 git 是權威,沒進 git 的檔必然晚於祖父日;Agentheim 讀的是 frontmatter,沒日期才真的
分不出來。git 本身跑不動(不是 repo / 沒 git)才是「無法判定」:跟日期有關的規則整條不適用,
印出來,不動離開碼。

離開碼(照 `PIPELINE.md` 那張表):
    0  沒有待處理項(祖父豁免與佇列不算)
    1  有待處理項(祖父=否的規則命中,或新票在祖父=是的規則上命中)
    2  用法錯誤(參數個數不對 / 吃錯目錄:沒有 `.scratch/ddd-harness/issues/`)
    3  **不適用** —— 一張票都沒掃到。不是通過,自成一類印最上面。

用法:
    python3 harness_lint.py <repo_root>
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

# 祖父日:這一天(含)以前首次 commit 的檔案不追溯。**永遠不要往前移。**
ADOPTION_DATE = "2026-08-25"

ISSUES_DIR = Path(".scratch/ddd-harness/issues")
SCRATCH_DIR = Path(".scratch/ddd-harness")
EXAMPLES_DIR = Path("examples")
COUNT_DOCS = ("CLAUDE.md", "README.md", "tools/harness/PIPELINE.md")

# 規則名與「祖父條款適用嗎」。順序 = 報表順序。
RULES: tuple[tuple[str, bool], ...] = (
    ("ticket-filename", False),
    ("status-vocabulary", True),
    ("status-single-cell", True),
    ("prediction-before-result", False),
    ("prediction-before-run", True),
    ("referenced-run-exists", False),
    ("blocked-by-resolvable", True),
    ("convention-undecided", True),
    ("ticket-count-in-docs", False),
)
GRANDFATHERED_RULES = {name for name, gf in RULES if gf}
QUEUE_RULES = {"convention-undecided"}

# CLAUDE.md:新票只准前六個;`resolved` / `A 半 done` 只給祖父票。
STATUS_VOCAB = ("needs-triage", "needs-info", "blocked", "reopened", "done", "resolved", "A 半 done")
STATUS_VOCAB_NEW = STATUS_VOCAB[:5]
STATUS_VOCAB_LEGACY = STATUS_VOCAB[5:]

# ADR 0007 §4:立規的詞。這張表沒驗過假陽性率,所以它餵的是佇列不是判決。
CONVENTION_WORDS = ("慣例", "規約", "一律", "必須")
PROSE_ONLY_MARKER = "prose-only, unenforced"

TICKET_FILENAME = re.compile(r"^(\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
STATUS_LINE = re.compile(r"^\*\*Status:\*\*(.*)$")
BLOCKED_LINE = re.compile(r"^\*\*Blocked by:\*\*(.*)$")
TICKET_REF = re.compile(r"票\s*(\d{1,2})")
# `runs/<name>`:名字以字母數字開頭,遇到 `/`、空白、反引號、`<` 就停。
# 所以 `runs/ 底下`、`examples/**/runs/`、`runs/<name>` 都不會被當成引用。
RUN_REF = re.compile(r"runs/([0-9A-Za-z][0-9A-Za-z_.-]*)")
# 「27 張」「27 張票」「18 張還活著」「9 張已完成」—— 只查總數,活票數刻意不查(見 rule_ticket_count)。
COUNT_REF = re.compile(r"(\d+)\s*張(?:票)?(還活著|已完成)?")
NEXT_REF = re.compile(r"目前到\s*(\d+)\s*[,,]\s*下一張是\s*(\d+)")

DateProvider = Callable[[Path], Optional[str]]


@dataclass
class Finding:
    rule: str
    path: str            # 相對 root
    message: str
    grandfathered: bool  # True = 祖父豁免,不計入離開碼


@dataclass
class Ticket:
    path: Path
    rel: str
    number: Optional[int]
    text: str
    first_commit: Optional[str]   # ISO 日期;None = 還沒 commit
    lines: list[str] = field(default_factory=list)

    @property
    def is_new(self) -> bool:
        """祖父日之後首次 commit,或還沒 commit → 新票。"""
        return self.first_commit is None or self.first_commit > ADOPTION_DATE


@dataclass
class Report:
    findings: list[Finding]
    tickets_scanned: int
    new_tickets: int
    limits: list[str]          # 這次跑到的「無法判定」,印在上限節
    git_available: bool

    def active(self) -> list[Finding]:
        return [f for f in self.findings if not f.grandfathered and f.rule not in QUEUE_RULES]

    def exempt(self) -> list[Finding]:
        return [f for f in self.findings if f.grandfathered and f.rule not in QUEUE_RULES]

    def queue(self) -> list[Finding]:
        return [f for f in self.findings if f.rule in QUEUE_RULES]


class UsageError(Exception):
    pass


class GitUnavailable(Exception):
    pass


# ── git:首次 commit 日期 ─────────────────────────────────────────────────

def git_first_commit(root: Path) -> DateProvider:
    """回傳一個 `path → ISO 日期 | None` 的函式(None = 還沒 commit)。
    git 跑不動時丟 `GitUnavailable`,呼叫端決定怎麼降級。結果快取,一個檔只問一次。"""
    cache: dict[str, Optional[str]] = {}

    def provider(path: Path) -> Optional[str]:
        rel = str(path.relative_to(root)) if path.is_absolute() else str(path)
        if rel in cache:
            return cache[rel]
        try:
            proc = subprocess.run(
                ["git", "log", "--diff-filter=A", "--format=%cs", "--", rel],
                cwd=root, capture_output=True, text=True, check=False,
            )
        except (OSError, ValueError) as exc:
            raise GitUnavailable(f"git 跑不動:{exc}") from exc
        if proc.returncode != 0:
            raise GitUnavailable(proc.stderr.strip() or f"git log 離開碼 {proc.returncode}")
        dates = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
        cache[rel] = dates[-1] if dates else None   # 最早的一筆在最後
        return cache[rel]

    return provider


def dates_from_file(dates_file: Path) -> DateProvider:
    """測試用:從 `GIT-DATES.txt`(每行 `<相對路徑> <ISO 日期|uncommitted>`)假裝 git。
    fixture 本身的 git 日期全是同一天,分不出新舊,所以要用這個。"""
    table: dict[str, Optional[str]] = {}
    root = dates_file.parent
    for ln in dates_file.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        rel, date = ln.rsplit(maxsplit=1)
        table[rel] = None if date == "uncommitted" else date

    def provider(path: Path) -> Optional[str]:
        rel = str(path.relative_to(root)) if path.is_absolute() else str(path)
        return table.get(rel)

    return provider


def _later_than(a: Optional[str], b: Optional[str]) -> bool:
    """a 是否嚴格晚於 b;None(還沒 commit)當成無限晚。兩個都 None → 分不出 → False。"""
    if a is None:
        return b is not None
    if b is None:
        return False
    return a > b


# ── 讀資料(loss-tolerant) ────────────────────────────────────────────────

def _read(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def load_tickets(root: Path, dates: DateProvider, limits: list[str]) -> list[Ticket]:
    issues = root / ISSUES_DIR
    tickets: list[Ticket] = []
    for path in sorted(issues.iterdir()):
        if not path.is_file() or path.suffix != ".md":
            continue
        text = _read(path)
        if text is None:
            limits.append(f"{path.relative_to(root)}:讀不到,整張跳過(不標)")
            continue
        m = TICKET_FILENAME.match(path.name)
        number = int(m.group(1)) if m else None
        try:
            first = dates(path)
        except GitUnavailable:
            first = ADOPTION_DATE  # 分不出來 → 當祖父,不標
        tickets.append(Ticket(path, str(path.relative_to(root)), number, text, first, text.splitlines()))
    return tickets


def run_dirs(root: Path) -> dict[str, list[str]]:
    """`examples/**/runs/<name>` → name 對到所有出現的相對路徑(同名可以在不同 examples 底下)。"""
    found: dict[str, list[str]] = {}
    base = root / EXAMPLES_DIR
    if not base.is_dir():
        return found
    for runs in sorted(base.rglob("runs")):
        if not runs.is_dir():
            continue
        try:
            children = sorted(p for p in runs.iterdir() if p.is_dir())
        except OSError:
            continue
        for child in children:
            found.setdefault(child.name, []).append(str(child.relative_to(root)))
    return found


def status_lines(t: Ticket) -> list[str]:
    return [m.group(1) for ln in t.lines if (m := STATUS_LINE.match(ln))]


def first_status_word(status: str) -> Optional[str]:
    """`**blocked** —— ...` → `blocked`;`**A 半 done**(...` → `A 半 done`;不在詞表 → None。"""
    text = status.strip().lstrip("*").strip()
    for word in sorted(STATUS_VOCAB, key=len, reverse=True):
        if text.startswith(word):
            rest = text[len(word):]
            if not rest or not (rest[0].isalnum() or rest[0] in "-_"):
                return word
    return None


# ── 九條規則 ─────────────────────────────────────────────────────────────

def rule_ticket_filename(tickets: list[Ticket]) -> list[Finding]:
    out: list[Finding] = []
    by_number: dict[int, list[Ticket]] = {}
    for t in tickets:
        if t.number is None:
            out.append(Finding("ticket-filename", t.rel, "檔名不是 `NN-kebab-slug.md`", False))
        else:
            by_number.setdefault(t.number, []).append(t)
    for number, group in sorted(by_number.items()):
        if len(group) > 1:
            names = ", ".join(g.path.name for g in group)
            for g in group:
                out.append(Finding("ticket-filename", g.rel, f"票號 {number:02d} 重號:{names}", False))
    return out


def rule_status_vocabulary(tickets: list[Ticket]) -> list[Finding]:
    out: list[Finding] = []
    for t in tickets:
        lines = status_lines(t)
        if not lines:
            continue  # 沒有 Status 行歸 status-single-cell 管
        word = first_status_word(lines[0])
        if word in STATUS_VOCAB_NEW:
            continue
        if word is None:
            head = lines[0].strip()[:40]
            msg = f"Status 第一個詞不在詞表裡:`{head}`(新票只准 {' / '.join(STATUS_VOCAB_NEW)})"
        else:
            msg = f"Status 用了 `{word}` —— 只給祖父票;新票只准 {' / '.join(STATUS_VOCAB_NEW)}(`resolved` → `done`)"
        out.append(Finding("status-vocabulary", t.rel, msg, not t.is_new))
    return out


def rule_status_single_cell(tickets: list[Ticket]) -> list[Finding]:
    out: list[Finding] = []
    for t in tickets:
        n = len(status_lines(t))
        if n == 1:
            continue
        msg = "沒有 `**Status:**` 行" if n == 0 else f"有 {n} 個 `**Status:**` 行 —— 整格重寫,不追加"
        out.append(Finding("status-single-cell", t.rel, msg, not t.is_new))
    return out


def rule_prediction_before_result(root: Path, dates: DateProvider, limits: list[str]) -> list[Finding]:
    out: list[Finding] = []
    scratch = root / SCRATCH_DIR
    for result in sorted(scratch.glob("*-RESULT.md")):
        stem = result.name[: -len("-RESULT.md")]
        prediction = scratch / f"{stem}-PREDICTION.md"
        rel = str(result.relative_to(root))
        if not prediction.is_file():
            out.append(Finding("prediction-before-result", rel, f"有 RESULT 卻沒有 `{prediction.name}`", False))
            continue
        try:
            r_date, p_date = dates(result), dates(prediction)
        except GitUnavailable:
            limits.append(f"prediction-before-result:git 不可用,`{stem}` 那對無法比先後(不標)")
            continue
        if r_date is None and p_date is None:
            limits.append(f"prediction-before-result:`{stem}` 兩份都還沒 commit,分不出先後(不標)")
            continue
        if _later_than(p_date, r_date):
            out.append(Finding(
                "prediction-before-result", rel,
                f"`{prediction.name}` 首次 commit({p_date or '未 commit'})晚於 RESULT({r_date})—— 預測寫在跑之後不算數",
                False))
    return out


def rule_prediction_before_run(root: Path, tickets: list[Ticket], runs: dict[str, list[str]],
                               dates: DateProvider, limits: list[str]) -> list[Finding]:
    out: list[Finding] = []
    scratch = root / SCRATCH_DIR
    for t in tickets:
        if t.number is None:
            continue
        prediction = scratch / f"{t.number:02d}-PREDICTION.md"
        if not prediction.is_file():
            continue  # 沒預測檔就沒有基準;要不要有預測檔不是這條管的
        refs = sorted(set(RUN_REF.findall(t.text)))
        if not refs:
            continue
        try:
            p_date = dates(prediction)
            for name in refs:
                for rel_dir in runs.get(name, []):
                    r_date = dates(root / rel_dir)
                    if _later_than(p_date, r_date):
                        out.append(Finding(
                            "prediction-before-run", t.rel,
                            f"`{rel_dir}` 首次 commit({r_date or '未 commit'})早於 `{prediction.name}`({p_date or '未 commit'})",
                            not t.is_new))
        except GitUnavailable:
            limits.append(f"prediction-before-run:git 不可用,票 {t.number:02d} 無法比先後(不標)")
    return out


def rule_referenced_run_exists(tickets: list[Ticket], runs: dict[str, list[str]]) -> list[Finding]:
    out: list[Finding] = []
    for t in tickets:
        for name in sorted(set(RUN_REF.findall(t.text))):
            if name not in runs:
                out.append(Finding("referenced-run-exists", t.rel,
                                   f"引用 `runs/{name}`,但 `examples/**/runs/` 底下沒有這個目錄", False))
    return out


def rule_blocked_by_resolvable(tickets: list[Ticket]) -> list[Finding]:
    numbers = {t.number for t in tickets if t.number is not None}
    out: list[Finding] = []
    for t in tickets:
        for ln in t.lines:
            m = BLOCKED_LINE.match(ln)
            if not m:
                continue
            for ref in TICKET_REF.findall(m.group(1)):
                if int(ref) not in numbers:
                    out.append(Finding("blocked-by-resolvable", t.rel,
                                       f"`Blocked by` 提到票 {ref},但沒有這張票", not t.is_new))
    return out


def rule_convention_undecided(tickets: list[Ticket]) -> list[Finding]:
    """ADR 0007 §4:有立規的詞、卻既沒指規則名也沒寫 prose-only → 佇列(不是判決)。
    「指了規則名」放寬成:任一條已登記的規則名、或 `harness_lint` 這個字串 —— 新票交新規則時,
    規則名還不在這張表裡。"""
    rule_names = tuple(name for name, _ in RULES) + ("harness_lint",)
    out: list[Finding] = []
    for t in tickets:
        words = [w for w in CONVENTION_WORDS if w in t.text]
        if not words:
            continue
        if PROSE_ONLY_MARKER in t.text or any(r in t.text for r in rule_names):
            continue
        out.append(Finding("convention-undecided", t.rel,
                           f"含立規詞 {'/'.join(words)},但沒指 `harness_lint` 規則名、也沒寫「{PROSE_ONLY_MARKER}」",
                           not t.is_new))
    return out


def rule_ticket_count(root: Path, tickets: list[Ticket]) -> list[Finding]:
    """只查**總數**與「目前到 N,下一張是 N+1」。「N 張還活著 / 已完成」刻意不查:
    「活著」的定義沒拍板(`A 半 done` 算哪邊?),而這條祖父=否,查了就是每關一張票逼三份文件。"""
    total = len(tickets)
    numbers = [t.number for t in tickets if t.number is not None]
    highest = max(numbers) if numbers else 0
    out: list[Finding] = []
    for doc in COUNT_DOCS:
        text = _read(root / doc)
        if text is None:
            continue  # 讀不到就不標
        for i, ln in enumerate(text.splitlines(), 1):
            # 「N 張」太泛(什麼都能論張),只認同一行有講到票的;「目前到 N」形狀夠專一,不用這道濾網
            for m in COUNT_REF.finditer(ln) if ("票" in ln or "issues" in ln) else ():
                if m.group(2):
                    continue  # 還活著 / 已完成:不查
                if int(m.group(1)) != total:
                    out.append(Finding("ticket-count-in-docs", f"{doc}:{i}",
                                       f"寫「{m.group(1)} 張」,實際 {total} 張", False))
            for m in NEXT_REF.finditer(ln):
                if int(m.group(1)) != highest or int(m.group(2)) != highest + 1:
                    out.append(Finding("ticket-count-in-docs", f"{doc}:{i}",
                                       f"寫「目前到 {m.group(1)},下一張是 {m.group(2)}」,實際到 {highest:02d},下一張 {highest + 1:02d}",
                                       False))
    return out


# ── 組起來 ────────────────────────────────────────────────────────────────

def lint(root: Path, dates: Optional[DateProvider] = None) -> Report:
    """吃 root,吐 Report。不寫任何東西。`dates` 不給就問 git。"""
    root = root.resolve()
    if not (root / ISSUES_DIR).is_dir():
        raise UsageError(f"吃錯目錄:{root} 底下沒有 {ISSUES_DIR}")
    limits: list[str] = []
    git_available = True
    if dates is None:
        dates = git_first_commit(root)
        try:
            dates(root / "CLAUDE.md")
        except GitUnavailable as exc:
            git_available = False
            limits.append(f"git 不可用({exc})—— 祖父條款無法判定,祖父=是的規則全當祖父(不標);"
                          "prediction-before-* 兩條整條不適用")
    tickets = load_tickets(root, dates, limits)
    runs = run_dirs(root)
    findings: list[Finding] = []
    findings += rule_ticket_filename(tickets)
    findings += rule_status_vocabulary(tickets)
    findings += rule_status_single_cell(tickets)
    findings += rule_prediction_before_result(root, dates, limits)
    findings += rule_prediction_before_run(root, tickets, runs, dates, limits)
    findings += rule_referenced_run_exists(tickets, runs)
    findings += rule_blocked_by_resolvable(tickets)
    findings += rule_convention_undecided(tickets)
    findings += rule_ticket_count(root, tickets)
    return Report(findings, len(tickets), sum(t.is_new for t in tickets), limits, git_available)


def render(report: Report, root: Path) -> str:
    lines = [f"\n=== harness_lint:{root} ===",
             f"掃到 {report.tickets_scanned} 張票(祖父日 {ADOPTION_DATE},嚴格之後才算新;新票 {report.new_tickets} 張)"]
    if report.tickets_scanned == 0:
        lines.append("\n【不適用】—— 不是通過,一張票都沒掃到,規約這次沒有被檢查過(離開碼 3)")
        return "\n".join(lines)

    active, exempt, queue = report.active(), report.exempt(), report.queue()
    lines.append(f"\n待處理 {len(active)} 筆(計入離開碼)/ 祖父豁免 {len(exempt)} 筆 / 佇列 {len(queue)} 筆(後兩者不計入)\n")
    lines.append("逐條:  規則                        待處理  祖父豁免")
    for name, gf in RULES:
        if name in QUEUE_RULES:
            n = sum(f.rule == name for f in queue)
            lines.append(f"  {name:<28}{'佇列':>6} {n:>5}(祖父 {sum(f.rule == name and f.grandfathered for f in queue)})")
            continue
        a = sum(f.rule == name for f in active)
        e = sum(f.rule == name for f in exempt)
        lines.append(f"  {name:<28}{a:>6} {e:>9}{'' if gf else '   (祖父 否)'}")

    if active:
        lines.append("\n❌ 待處理:")
        for f in active:
            lines.append(f"  [{f.rule}] {f.path}\n      {f.message}")
    if exempt:
        lines.append("\n⏭️ 祖父豁免(舊票不追溯改,ADR 0007 §2):")
        for f in exempt:
            lines.append(f"  [{f.rule}] {f.path}\n      {f.message}")
    if queue:
        lines.append("\n📋 分診佇列 convention-undecided(ADR 0007 §4;**佇列不是判決**,人去讀):")
        for f in queue:
            lines.append(f"  {'(祖父)' if f.grandfathered else '      '} {f.path}\n      {f.message}")

    lines.append("\n--- 這份報表的上限(讀之前先看)---")
    lines.append("* 「新舊」看 git 首次 commit,不看 mtime;同一 commit 一起進來的 PREDICTION / RESULT / run"
                 " **分不出先後**(相等算通過)—— 「先跑再補預測但一起 commit」抓不到。")
    lines.append(f"* 祖父日**當天**({ADOPTION_DATE})commit 的檔也算祖父;lint 對當天進 repo 的票沒有牙。")
    lines.append("* `convention-undecided` 的關鍵字表沒量過假陽性率;它抓「忘了決定」,抓不到「決定錯了」。")
    lines.append("* `ticket-count-in-docs` 只查總數;「N 張還活著 / 已完成」不查(定義沒拍板)。")
    for lim in report.limits:
        lines.append(f"* 這次跑到的:{lim}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    root = Path(argv[1])
    try:
        report = lint(root)
    except UsageError as exc:
        print(exc, file=sys.stderr)
        return 2
    print(render(report, root.resolve()))
    if report.tickets_scanned == 0:
        return 3
    return 1 if report.active() else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
