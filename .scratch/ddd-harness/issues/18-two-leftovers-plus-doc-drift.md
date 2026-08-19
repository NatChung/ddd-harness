# 18 — 票 14 剩下的兩條 + 文件跟現況漂了

**What to build:** 兩個小修 + 兩份文件更新。**都有先例可循,不需要新的設計決定。**

**Blocked by:** None

**Status:** **done**(2026-08-19,209 passed)

## 一、`gen_archunit._base_package` 還有一個 `SystemExit` 在 `generate()` 裡

`tools/harness/gen_archunit.py:200`:

```python
raise SystemExit("來源 package 沒有共同前綴,無法決定 importPackages 的根")
```

跟票 14 修掉的是**同一種病**(`generate()` 是函式,被 import 進來當函式呼叫時,
`SystemExit` 會把呼叫方整支打死),只是觸發條件不同:**有規則,但 from 側各值沒有共同的
點號分段前綴**。票 14 當時說「該歸『錯誤』還是『規格有問題』要先定案」,所以沒動。

**⚠️ 現在有先例了,照抄就好。** `package_landing_check.py` 對**逐字同一個情況**已經定了:

> **exit 3 —— 整份不適用**:(a) 一條都沒宣告 (b) root 沒對上任何宣告 **(c) 宣告全是萬用字元**

也就是「推不出共同前綴」在那支是 **不適用**,不是錯誤。**`gen_archunit` 沿用同一個語意**,
不要另外發明。

做法方向:比照票 14 的 `NothingToGenerate`,但這是**不同的原因**(不是「沒東西可生成」,
是「有東西但決定不了根」)—— 要嘛擴充那個例外帶原因,要嘛新增一個同層的例外。
⚠️ **不論哪一種,`verify_generated.py` 的呼叫端都要跟著處理**,否則只是把 crash 換一個名字。

## 二、`README.md` L83 的 `verify_generated` 範例參數是反的

傳了 yaml 當 `generated_dir`、傳了 `.java` 當 spec。**那條指令從來不可能跑得起來。**
照 `verify_generated.py` 的 usage 改對,並**實際跑一次確認它會過**。

## 三、`PIPELINE.md` 幕四那格已經跟現況漂了

它還寫著:

> ❌ **從來沒有任何實作照這條管線產出的規格寫過。**
> **這是「完整跑通一次」唯一缺的那塊,也是 MISSION 的頭號測試。**

**2026-08-19 跑過了**(`runs/2026-08-19-act4/`,38 turns / 14.4 分 / $6.32,9/9 全綠)。

要改成**現況 + 誠實的但書**,而不是改成「✅ 驗過了」:

- ✅ 管線閉環:一句話 → 30 題 → 550 行規格 → 5 條情境 → 9 條測試全綠 + 23 個實作 class
- ⚠️ **但「全綠」只證明了 1 條真情境**(其餘 4 條是代理編碼,不算驗收);
  17 條 GWT 只有 1 條、17 條契約只有 8 條走到實作面前
- ⚠️ **架構那 4 條是凍結骨架繼承來的**,不是這份規格生的(§9 的 10 條一條都沒落檔,票 16)
- ⚠️ **只有一份實作** —— MISSION 要的「兩個模型都被同一套驗收判定」還沒做到
- 證據:`runs/2026-08-19-act4/RESULT.md` 與 `runs/2026-08-19-act2/RESULT.md`

**每一段的「驗過沒有」欄要照實更新**,幕一/幕二也要補這一跑(真人需求方那場)。

## 四、`README.md` 少了 2026-08-18 之後新增的檢查

至少這幾支沒有出現在 README:`landing_check.py`、`contract_triage.py`、`glossary_check.py`、
`package_landing_check.py`、`run_act4.sh`。⚠️ **先自己掃一遍 `tools/harness/` 對照**,
不要只照這張清單(這張清單本身可能也漏)。

## 硬約束

- ⚠️ **不准改**:`examples/shop/app/`、`examples/shop/spec/`、`examples/shop/app-from-interview/`、
  `tools/harness/interview-prompt.md`、`examples/shop/harness/act1/`、
  **`tools/harness/run_act2.sh`(票 16 正在動)**、`lessons/`(票 17 正在動)、
  以及 `examples/shop/harness/runs/` 底下**任何**檔案(那些是量測產物,動了就沒得比)。
- `python3 -m pytest tools/harness -q` 要全綠(**基線 206 passed**)。
- 第一條要**先證明它原本會漏**(貼指令 + 輸出),再修,再確認同一個情況現在走對的路徑。
  破壞式驗證要先印 `mutated ok`。

## 不用寫預測

第一條有先例、第二條是錯字、三四是文件對照現況。**這張票沒有值得賭的假設。**
(若你在做的過程中發現有值得賭的東西,回報時講,不要自己補一份事後預測。)

---

## 2026-08-19 · 落地(209 passed,基線 206 + 3 條新測試)

**一、`_base_package` 的 `SystemExit`** —— 改丟 `NothingToGenerate`(**沿用票 14 那個例外,
不新增型別**),成因寫進訊息;`spec_store` 的 docstring 補上「不只一種形狀」那段。
歸「不適用」是照 `package_landing_check` 的先例,沒有發明新語意。
`verify_generated` 的 `except NothingToGenerate` 因此同時接住兩種成因 —— 但那條
unbacked 的解說原本寫死「沒有 spec 撐著」,對新成因是假話,一併改掉。

原本會漏的證明(修前):`gen_archunit` exit 1;`verify_generated` **stdout 0 byte、exit 1**
—— 跟「生成物漂了」的 1 一模一樣,而且**另外那個生成器也一起停擺**。
修後:兩支都 exit 3、報表印出【不適用】那一段;把 `ArchitectureTest.java` 塞回
`generated_dir`(先印 `mutated ok`)→ exit 1(unbacked 蓋過不適用)。

**二、README L83** —— `verify_generated` 的兩個參數是反的,已改成
`<generated_dir> <spec1.yaml> <spec2.yaml>`,實跑 exit 0(`ok: 生成物與 spec 一致`)。
順帶補上原本缺的 `gen_acceptance.py` 呼叫,並把 store 的 import 改成兩份 yaml 一起進
—— 否則 `gen_acceptance` 沒有情境可吃。

**三、`PIPELINE.md`** —— 幕四那格改成「跑通了 + 四條但書」,一張圖那格、章節標題、
「現在缺的三塊」第 3 點一併更新;幕一補真人需求方那一跑(**加,沒動「opus 沒跑過」
那條 ❌** —— `run-meta.json` 記的訪談者是 subagent 不是 opus,而且刻意少給一份輸入,
不能拿來抵);幕二補 2026-08-19 那跑與它的主發現;幕三補 act4 的逐位元組佐證;
幕五補「幕四那半還沒閉環」。

**四、README 少的檢查** —— 自己掃一遍的結果跟票裡那張清單**不一樣**:
`contract_triage.py` / `glossary_check.py` **本來就在 README**(各 2、4 處);
`landing_check.py` / `run_act4.sh` 屬幕一/幕四,**PIPELINE 已有**,而 README 自己第一行
就寫「只講第三幕的生成器」—— 塞進去反而破壞它的範圍。真正的洞只有兩個:
**`package_landing_check.py`(兩份文件都沒有)** 與 **`gen_acceptance.py`(README 只在
ASCII 圖裡出現過,沒有任何可執行的呼叫)**。兩個都補了。

### 順帶記下(不在本票範圍)

`PIPELINE.md` 的「開著的票」那段還停在 01–09,而現在已經開到 18(票 10–14 已完成、
15/16/17 進行中)。本票刻意沒動它 —— 票 16、17 正在動別的檔,那段留給收尾的人。
