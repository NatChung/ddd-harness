# 14 — 兩個已確認的檢查缺陷(離開碼會翻綠 / drift check 整支 crash)

**What to build:** 修兩個已經重現過的缺陷。兩個都不是新功能,是已交付工具的洞。

**Blocked by:** None

**Status:** **done**(2026-08-19,commit `215ae8c`)—— 兩個缺陷已修,離開碼語意統一成一張跨四支檢查的表。檔末另記三條回報未修的。

## 缺陷一:`verify_generated.py` 對「沒有架構規則的 store」整支 crash

`verify_generated.py:35` 把 `gen_archunit.generate` **import 進來當函式呼叫**,
而 `gen_archunit.py:237` 在查不到規則時 `raise SystemExit("store 裡沒有生成得出來的規則…")`。
當 CLI 沒問題,被 import 就把整支 drift check 打死 —— stdout 一行都沒印、exit 1。

**後果:任何「沒有 architecture_rule」的 store 都做不了 drift check**,
而票 10 那份骨架的 store 正是。**生成物有沒有被手改過,今天量不到。**

(票 10 當時沒修,因為票 11 正在動 `tools/harness/`;它改用等價做法
—— 重生一份到 temp 跟骨架裡那兩支 `diff`,兩支 byte-identical。)

修法方向:`generate()` 是函式,不該用 `SystemExit` 表達「沒東西可生成」。
⚠️ 但要分清楚**兩種**「沒東西」:store 真的沒有規則(這份骨架的情況,應該是**不適用**)
vs 呼叫方式錯了(應該是錯誤)。**不要把它們折成同一個結果** —— 那正是票 11 踩過的坑。

## 缺陷二:`package_landing_check.py` 的 `--root` 打錯會讓離開碼翻綠

`--root` 打錯一個字母(`com.shop` → `com.shopp`)→ 所有自有 package 被歸成第三方
→ **離開碼從 1 變成 0**。

那支的上限段已經明寫這個失效模式(root 推導 / 排除清單會被印出來),
**但沒說離開碼會翻綠** —— 而翻綠才是會騙到人的那半。

修法方向:離開碼要有一個值表示「**root 沒對上任何 class,這次什麼都沒檢查到**」。
現有的碼:`1` = 不適用/有問題、`2` = 用法錯誤、`3`(`landing_check` 用)= 整份不適用。
**沿用同一套語意**,不要各支自己發明。

## 紀律

- 兩個都要**先證明它原本會漏**(貼指令 + 輸出),再修,再確認同一個破壞現在會紅。
- 破壞式驗證要先確認**破壞本身生效了**(印 `mutated ok`)。
- 不要為了讓數字好看而把「不適用」折進「通過」或「錯誤」。

---

## 2026-08-19 · 落地(commit `215ae8c`,206 passed)

兩個都修了,而且**離開碼語意統一成一張表**(見 commit message)。做法:新增
`spec_store.NothingToGenerate`(放在 `SpecError` 旁),三處 `SystemExit` 全改;
`verify()` 改回傳 `Result(drift / not_applicable / unbacked)`;目錄不見走新的
`UsageError` —— **不**用 `SystemExit`,因為這支自己就是被函式裡的 `SystemExit` 害到的呼叫方。

⚠️ **給下一個稽核的人**:票 10 的凍結預測 P4 寫著 `ArchitectureTest.java` 會
「空對空地過(✅)」。現在它報 **◻ 不適用**,這是**刻意背離**(ADR 0005 §6:
不適用不准折進通過),**不是回歸**。

### 三個回報但未修的(不在本票範圍,先記下來免得只活在對話裡)

1. ⚠️ **`gen_archunit._base_package` 還有一個 `raise SystemExit("來源 package 沒有共同前綴…")`,
   而且在 `generate()` 裡面** —— 跟本票修的是**同一種病**(import 進來就把呼叫方打死),
   只是觸發條件不同:有規則、但 from 側各值沒有共同的點號分段前綴。
   它不是「沒東西可生成」,所以沒折進 `NothingToGenerate`。
   **它該歸「錯誤」還是「規格有問題」要先定案。**
2. **`README.md` L83 的 `verify_generated` 範例參數是反的** —— 傳了 yaml 當
   `generated_dir`、傳了 `.java` 當 spec。**那條指令從來不可能跑得起來。**
3. **drift check 看不見「沒有任何生成器認領的 `.java`」** —— 手工加一個檔進
   `generated_dir`,它對 drift check 完全隱形(`GENERATORS` 是白名單,不掃目錄)。

---

## 2026-08-19 稍晚 · 檔末那三條的下落

- **(a) `gen_archunit._base_package` 的 `SystemExit`** —— ✅ **已由票 18 修掉**(commit `9c49fb2`)。
  沿用本票的 `NothingToGenerate`(不新增型別),語意照 `package_landing_check` 的先例判
  **exit 3 整份不適用**;`verify_generated` 的呼叫端三條路徑都跟著處理了,不是換個名字的 crash。
- **(b) `README.md` L83 的範例參數反了** —— ✅ **已由票 18 修掉**,而且重寫後那段 bash **每一行都實跑過**。
- **(c) drift check 看不見「沒有任何生成器認領的 `.java`」** —— ⚠️ **仍未修**。
  `GENERATORS` 是白名單、不掃目錄。**這條要決定**(要不要改成掃目錄),不是照先例就能做,
  所以票 18 沒碰。票 18 順帶把它寫進了 `PIPELINE.md` 幕三的「已知盲區」。
