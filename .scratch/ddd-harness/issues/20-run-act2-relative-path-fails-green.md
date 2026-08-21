# 20 — `run_act2.sh` 吃相對路徑會失敗,而離開碼還是 0

**What to build:** 讓 `run_act2.sh` 對相對路徑要嘛正確運作、要嘛當場報錯,
**不要失敗成綠的**。

## 重現(2026-08-21 timesheet 第二幕實測)

```bash
tools/harness/run_act2.sh examples/.../SPEC-draft.md examples/.../2026-08-21-act2 opus
# → run_act2.sh: line 170: examples/.../2026-08-21-act2/result.json: No such file or directory
# → rc=1:沒有產出 acceptance.yaml
# → $? == 0
```

原因在最後那段:

```bash
cd "$WORK" || exit 90
env -i … bash -c 'cd "$WORK"; claude -p …' > "$WORK/result.json" 2> "$WORK/stderr.log"
```

外層先 `cd "$WORK"`,**重導向才展開** `"$WORK/result.json"` —— 相對路徑此時已經對不到。
內層 `bash -c` 的 `cd "$WORK"` 同理再錯一次。

**真正貴的是最後一行**:

```bash
[ -f "$WORK/acceptance.yaml" ] && echo "ok: …" || echo "rc=$rc:沒有產出 acceptance.yaml"
```

`echo` 成功,所以**整支 script 的離開碼是 0**。訊息說「沒有產出」,而機器讀到的是「通過」。
⚠️ 這正是本 repo 反覆抓的那一類:**報表說失敗,離開碼說成功**
(票 14 修過同型的一個:`--root` 打錯會讓離開碼翻綠)。

## 做法

| | 做法 | note |
|---|---|---|
| A | 開頭把 `SPEC` / `WORK` 都 `realpath` 成絕對路徑 | 一行,治根 |
| B | 最後一行 `|| { echo …; exit 1; }`,離開碼跟著結果走 | **必做**,跟 A 無關 |

**A 與 B 都要做。** 只做 A 的話,下次換一種失敗法又會靜靜翻綠。

## 附:長跑要防睡眠(不是 harness 缺陷,但同一次踩到)

第一次跑掛在 `Your computer went to sleep mid-response`(`terminal_reason: api_error`,
10 turns / $0.85 全丟)。機器當時在電池上、`pmset sleep 1`。
第二幕與第四幕都是 15–25 分鐘的跑,**要包 `caffeinate -ims`**。
⚠️ `caffeinate` 擋不住闔蓋。要不要寫進 runner 或只寫進文件,一併裁決。

**Blocked by:** None

**Status:** **needs-triage** —— 2026-08-21 跑 timesheet 第二幕當場踩到,
證據見 `examples/timesheet/harness/runs/2026-08-21-act2/RESULT.md` 檔末。

- [ ] 相對路徑要嘛能跑、要嘛當場報錯
- [ ] 「沒有產出 acceptance.yaml」時離開碼非 0
- [ ] 長跑防睡眠的處置有裁決(寫進 runner or 寫進文件)
