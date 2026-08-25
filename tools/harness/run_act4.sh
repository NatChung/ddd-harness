#!/bin/bash
# 第四幕的可重跑版:餵一份散文規格 + 一個骨架,拿回一份實作。
#
#   ./run_act4.sh <散文規格.md> <骨架目錄> <工作目錄> [model]
#
# 例:
#   ./run_act4.sh examples/shop/harness/runs/2026-08-18-act2-from-interview/input-SPEC.md \
#                 examples/shop/app-from-interview \
#                 examples/shop/harness/runs/2026-08-19-act4-from-interview
#
#   ACT4_DRY_RUN=1 ./run_act4.sh ...   # 只組工作目錄,不呼叫 claude(不花錢)
#
# ⚠️ **底下那段 heredoc prompt 是受測品。** 改了它,後續的跑就不能跟先前比 ——
#    跟 interview-prompt.md / act1/ 三份 / run_act2.sh 的 heredoc / 骨架本身
#    是同一種性質(ADR 0006 §6)。每次跑都會在工作目錄留下 prompt.txt,
#    **寫報告前先 diff 上一跑那份**;骨架的 blob 雜湊同樣每跑留一份
#    (harness/skeleton-blobs.txt),一起 diff。
#
# 隔離:bare dir,只有**散文規格 + 骨架**。
# **不放生成器、不放 spec store、不放任何既有實作、不放 examples/shop/app/** ——
# 凍結那份是答案卷,agent 讀得到就白測了。骨架自己的 build/ 與 .gradle/ 也不複製
# (那裡面有上一跑的測試結果)。
#
# ---------------------------------------------------------------------------
# 已知上限(ADR 0006;不要只寫在票裡,也不要寫進 agent 讀得到的 prompt)
#
# 1. **結構隔離不是防竄改。** `test` task 只跑生成的那三個 class(按 class 名釘死),
#    所以 agent 自己寫的測試**預設**進不了「完成的定義」。但工作目錄裡的
#    build.gradle 是可寫的 —— agent 刪掉那段 filter,它的測試就回到 test 裡。
#    擋不住,只查得出來:注入之後算一次雜湊基線,跑完再算一次,落 tamper-check.txt。
#    ⚠️ 基線必須算在**注入之後**,否則第一個被抓到的是 runner 自己。
# 2. **內圈測試靠方法名帶契約編號指認自己**(`C4_…`)—— 那是一條約定,
#    隨便一條測試取名 `C1_xxx` 就通過。只證明落點存在,**不證明那條測試真的在驗 C1**。
# 3. **架構那套不是這份規格擁有的**,是從凍結骨架繼承來的(store 生不出任何
#    architecture_rule,散文自己寫「機械檢查一條都沒有」)。空骨架階段它 4 條全綠、
#    而且 that() 命中 0 個 class → **報告記「不適用」,不是「通過」**(ADR 0006 §1)。
# 4. **package 形狀是骨架發明的,不是規格宣告的。** class 放到別的 package,
#    整套架構檢查會靜靜地不適用 —— 綠燈看起來跟完全遵守一模一樣。
#    prompt 裡把它寫成**正向要求**(三個 package 完成時都要有 class);
#    補這個坑的機械檢查是票 11 的 package_landing_check.py,不是本 runner。
# 5. **外部替身(HTTP 假服務,ADR 0006 §2)本 runner 未涵蓋。**
#    它是 act1-opus-rerun/SPEC-draft.md 那份規格要的,而那份一條情境都沒落檔、
#    生不出任何測試。這份規格三個獨立證據說它用不到(見 .scratch/ddd-harness/10-RESULT.md)。
# 6. **prompt 本身是新的一片洩題面** —— 它寫死了 package 名、任務結構與方法論。
#    骨架的洩題面清單見 .scratch/ddd-harness/10-PREDICTION.md 最後一節。
# ---------------------------------------------------------------------------
set -u

if [ $# -lt 3 ]; then
  echo "用法:$0 <散文規格.md> <骨架目錄> <工作目錄> [model]" >&2
  exit 64
fi

SPEC="$1"; SKEL="$2"; WORK="$3"; MODEL="${4:-opus}"
DRY="${ACT4_DRY_RUN:-0}"
HARNESS="$(cd "$(dirname "$0")" && pwd)"

[ -f "$SPEC" ] || { echo "找不到散文規格:$SPEC" >&2; exit 66; }
[ -d "$SKEL" ] || { echo "找不到骨架目錄:$SKEL" >&2; exit 66; }
SKEL_ABS="$(cd "$SKEL" && pwd)"
SPEC_ABS="$(cd "$(dirname "$SPEC")" && pwd)/$(basename "$SPEC")"

# ---- 0. 閘門(票 21):幕三的檢查證據 ---------------------------------------
# 帳本住在**骨架目錄**(acceptance_gwt 的 workdir 跑之前可能還不存在,所以那支要
# `check.py --run-dir <骨架目錄> acceptance_gwt …` 明給)。要求 acceptance_gwt 有一筆 exit 0。
# ⚠️ 離開碼 3(不適用)不算通過;而 acceptance_gwt 對綁非 shop-frozen-v1 合約的 spec
#    第 2、3 段一定不適用 → 整支回 3 → 這道閘門對那些 spec **只能靠 ACT_GATE_SKIP 過**,
#    直到 acceptance_gwt 能單獨回報第一段(改檢查器本體,不在票 21)。
# 閘門在 rm -rf "$WORK" **之前**:拒絕的話什麼都不動。dry-run 一樣要過閘門(閘門管的是順序,不是錢)。
if [ "${ACT_GATE_SKIP:-0}" = "1" ]; then
  [ -n "${ACT_GATE_SKIP_REASON:-}" ] || {
    echo "ACT_GATE_SKIP=1 需要 ACT_GATE_SKIP_REASON(沒理由不准跳)" >&2; exit 2; }
  echo "⚠️ 閘門跳過(ACT_GATE_SKIP=1):$ACT_GATE_SKIP_REASON"
  GATE_SKIPPED=true
else
  python3 "$HARNESS/check.py" --gate act4 "$SKEL_ABS" || exit $?
  GATE_SKIPPED=false
fi
GATE_REASON_JSON="$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1], ensure_ascii=False))' \
  "${ACT_GATE_SKIP_REASON:-}")"

# ---- 1. 組隔離工作目錄:骨架 + 散文規格,別的都不放 ------------------------
rm -rf "$WORK"; mkdir -p "$WORK"
WORK_ABS="$(cd "$WORK" && pwd)"
cp -R "$SKEL_ABS/." "$WORK_ABS/"
rm -rf "$WORK_ABS/build" "$WORK_ABS/.gradle"     # 上一跑的產物,不給看
rm -f "$WORK_ABS/check-ledger.jsonl"             # 骨架的帳本不帶進來:新跑新帳本(票 26 讀它)
mkdir -p "$WORK_ABS/spec" "$WORK_ABS/harness" "$WORK_ABS/src/innerTest/java"
cp "$SPEC_ABS" "$WORK_ABS/spec/SPEC.md"

# ---- 2. 注入內圈測試的結構隔離 ---------------------------------------------
# ⚠️ 這段也是受測品。凍結骨架不准改(它是 checked-in 的受測品),所以隔離是
#    **runner 注入到工作目錄那份複本**,不是改骨架本身 —— 刻意的決定,不是漂移。
#
# 兩片缺一不可(2026-08-19 用兩個誘餌實測過):
#   (a) 多一個 innerTest source set/task  → 內圈有地方住,而且 `test` 不會跑它
#   (b) `test` 按 class 名釘死            → agent 就算把測試塞進 src/test/java/acceptance/,
#                                            也不會跟著 `./gradlew test` 一起綠
# 只做 (a) 擋得住乖乖照規矩寫的 agent,擋不住把測試寫進 src/test/ 的。
cat > "$WORK_ABS/harness/inner-tests.gradle" <<'GRADLE'
// 由 harness 提供,實作者不得修改。
//
// 內圈測試(你自己寫的那些)住 src/innerTest/java,用 ./gradlew innerTest 跑。
// `test` task 只跑生成的那三個 class —— 那是完成的定義,內圈**不算進去**。
sourceSets {
    innerTest {
        java.srcDir 'src/innerTest/java'
        resources.srcDir 'src/innerTest/resources'
        compileClasspath += sourceSets.main.output
        runtimeClasspath += sourceSets.main.output
    }
}

configurations {
    innerTestImplementation.extendsFrom testImplementation
    innerTestRuntimeOnly.extendsFrom testRuntimeOnly
}

tasks.register('innerTest', Test) {
    group = 'verification'
    description = '內圈測試(實作者自己寫的)—— 不算進完成的定義'
    testClassesDirs = sourceSets.innerTest.output.classesDirs
    classpath = sourceSets.innerTest.runtimeClasspath
    useJUnitPlatform()
    testLogging {
        events 'passed', 'failed', 'skipped'
        exceptionFormat = 'short'
    }
}

// 完成的定義按 class 名釘死,不是按目錄。
tasks.named('test') {
    filter {
        includeTestsMatching 'acceptance.OrderAcceptanceTest'
        includeTestsMatching 'acceptance.OrderProxyAcceptanceTest'
        includeTestsMatching 'architecture.ArchitectureTest'
    }
}
GRADLE
printf "\n// 由 harness 注入(run_act4.sh)—— 實作者不得修改。\napply from: 'harness/inner-tests.gradle'\n" \
  >> "$WORK_ABS/build.gradle"

# ---- 3. 受測品紀律:骨架 blob 雜湊 + 受保護檔的雜湊基線 ---------------------
# 骨架在 repo 裡的樣子(ADR 0006 §6 第 2 條;寫報告前 diff 上一跑那份)
( cd "$SKEL_ABS" && git ls-files -s . ) > "$WORK_ABS/harness/skeleton-blobs.txt" 2>/dev/null \
  || echo "(骨架不在 git 裡,沒有 blob 雜湊)" > "$WORK_ABS/harness/skeleton-blobs.txt"

PROTECTED="build.gradle
settings.gradle
gradlew
gradle/wrapper/gradle-wrapper.properties
harness/inner-tests.gradle
src/main/java/com/shop/Application.java
src/main/resources/application.properties
src/test/java/acceptance/OrderAcceptanceTest.java
src/test/java/acceptance/OrderProxyAcceptanceTest.java
src/test/java/architecture/ArchitectureTest.java"

hash_protected() {
  ( cd "$WORK_ABS" && echo "$PROTECTED" | while read -r f; do
      [ -n "$f" ] || continue
      if [ -f "$f" ]; then shasum -a 256 "$f"; else echo "MISSING  $f"; fi
    done )
}
hash_protected > "$WORK_ABS/harness/protected-baseline.txt"   # ⚠️ 注入之後才算

# ---- 4. prompt(受測品)-----------------------------------------------------
cat > "$WORK_ABS/prompt.txt" <<'EOF'
你在做第四幕:實作。

骨架已經在這個目錄裡了:一個跑得起來的 Spring Boot 專案,`src/main/java/com/shop/`
底下**一個實作 class 都沒有**,而驗收測試已經寫好、現在全部是紅的。
你的工作是把實作填進去,填到驗收變綠。

讀這些檔:

  spec/SPEC.md                                        —— 規格。**唯一的真相來源。**
  src/test/java/acceptance/OrderAcceptanceTest.java   —— 驗收(生成物)
  src/test/java/acceptance/OrderProxyAcceptanceTest.java —— 驗收(生成物,代理編碼)
  src/test/java/architecture/ArchitectureTest.java    —— 架構檢查(生成物)

骨架已經替你決定了技術棧(Spring Boot / JPA / H2)與 package 形狀。那是**骨架**
帶進來的,不是規格說的 —— 照著做,但不要據此推論規格還說了別的。

---

## 一、完成的定義

    ./gradlew test

**全綠 = 完成。** 這個 task 只跑上面那三個 class(按 class 名釘死),它們是從規格生成的:

- `acceptance.OrderAcceptanceTest` —— 情境 S1 S2 S3 S4 S5 S6 S7 S11
- `acceptance.OrderProxyAcceptanceTest` —— 情境 S8 S9 S10 S12
- `architecture.ArchitectureTest` —— 四條相依性規則

規格〈完成的定義〉那一節寫的是「S1–S12 全綠」,S13 **不列入**(它是刻意留白的
阻斷級缺口,見下面第七節)。上面兩支驗收合起來就是 S1–S12。

**⚠️ 你自己寫的測試不算數。** 這不是請你自律 —— 是 build 的結構:`test` task
按 class 名只跑那三個,你新增的測試不管放在哪個目錄、取什麼 package 名,
都不會被 `test` 跑到,也就不可能把你送過關。內圈測試怎麼跑見第四節。

**⚠️ `OrderProxyAcceptanceTest` 那四條必須綠,但綠了不代表它宣稱的規格條文成立。**
那幾條的 fixture 不包含它的 Given/When 描述的那個動作(規格作者用別的東西近似它,
每個方法的 javadoc 都寫著覆蓋到哪一半)。它們仍然擋得住「連近似的那一半都壞了」,
所以要綠;但不要拿它們當「這條規格已經驗過」的證據。

**⚠️ 架構那套現在 4 條全綠,那不是通過,是「不適用」。** `com.shop.domain` /
`com.shop.usecase` / `com.shop.adapter` 底下一個 class 都沒有,四條規則掃不到任何
東西所以算過 —— 那四個綠燈裡沒有任何資訊。因此:

> **實作 class 必須落在 `com.shop.domain` / `com.shop.usecase` / `com.shop.adapter`
> 這三個 package 裡,而且完成的時候三個都要真的有 class。**

四條規則的內容(讀那個檔的 `@DisplayName`)就是你要遵守的分層方向:domain 與
usecase 不得依賴框架,domain 不得依賴 usecase/adapter,usecase 不得依賴 adapter。

---

## 二、不得修改的檔案

這些是骨架提供的,**一個位元組都不准改、不准刪、不准重新命名**:

    src/test/java/acceptance/OrderAcceptanceTest.java
    src/test/java/acceptance/OrderProxyAcceptanceTest.java
    src/test/java/architecture/ArchitectureTest.java
    src/main/java/com/shop/Application.java
    src/main/resources/application.properties
    build.gradle
    settings.gradle
    gradlew / gradle/wrapper/
    harness/inner-tests.gradle

跑完會用雜湊比對這些檔。**改了它們這一跑就作廢** —— 包括「只是加一行」、
「只是放寬一條斷言」、「只是加一個 @Disabled」。

驗收測試裡的期望值不准動。測試紅了,是實作要改,不是測試要改。

其他檔案你都可以新增:`src/main/java/com/shop/**` 底下的實作、
`src/main/resources/` 底下你需要的設定檔(不含上面列的那個)、`src/innerTest/java/**`
底下你自己的測試、根目錄的 `ASSUMPTIONS.md`。

---

## 三、做法:outside-in,一次一條

外圈 = 生成的驗收,現在全紅。內圈 = 你自己寫的測試。

迴圈:

1. **挑一條外圈紅的情境**(從 S1 開始,照編號往下)。**一次一條。**
2. 為了讓那一條變綠,你需要哪個物件做什麼 —— **在內圈寫一條紅的測試**,
   打在那個物件上(seam 怎麼找見第五節)。
3. 寫**最少的實作**讓那條內圈測試變綠。
4. 回頭跑外圈那一條。還紅就回第 2 步,再切一條內圈。
5. 外圈那一條綠了,才換下一條情境。

**不要先寫一堆測試再一起實作。** 一次一條 vertical slice —— 從 HTTP 進來到
落地再回去,窄窄一條打穿,再打下一條。

**refactor 不屬於這個迴圈。** 綠了以後才 refactor,而且 refactor 的時候
**不准改任何測試的期望值** —— 改了期望值那就不是 refactor。

---

## 四、內圈測試寫在哪、怎麼跑

    src/innerTest/java/**          —— 你自己的測試住這裡
    ./gradlew innerTest            —— 跑它們

內圈**不算進完成的定義**(第一節)。它存在的理由是:規格的〈契約〉表那 11 條
(C1–C11)是微尺度的規則,驗收只在 HTTP 層看得到它們的側影,**內圈測試才是那些
契約唯一的載體**。

**每條內圈測試的方法名要帶它在驗的那條契約編號**,例如:

    void C4_單價是下單當時的複本_商品調價後不變() { ... }
    void C6_數量必須是大於等於1的整數() { ... }

一條測試對到一條契約。收工時,C1–C11 每一條都要指得出至少一條內圈測試;
指不出來的那幾條,寫進 `ASSUMPTIONS.md` 說明為什麼(例如它守在別的地方、
或它是被規格擋掉的)。

---

## 五、seam 由規格指定,不是問人

**這是隔離跑,沒有人可以問。** 不要停下來確認,也不要在最後問「這樣可以嗎」。

「這條測試該打在哪個物件上」規格已經回答了:看 `spec/SPEC.md` 的〈契約〉表
(C1–C11),**「守在哪個聚合根內」那一欄就是答案** —— 那一欄寫「訂單」,
這條契約就守在訂單這個物件裡面,對應的內圈測試就打在訂單上,不是打在
controller、也不是打在 repository。

該欄標了 ⚠️ 的那條(C8,跨聚合根)照規格〈ASSUMPTIONS〉那一格的權宜作法落地,
**不得**據此新增聚合根或搬動邊界(見第七節)。

命名照〈詞彙表〉,**不得另創同義詞**;〈禁用同義詞清單〉那幾個講法不得裸用。

---

## 六、不准寫恆真(tautological)的測試

> **恆真的測試**:斷言用跟程式碼同樣的方式重算期望值,因此**依構造必然通過,
> 永遠不可能跟程式碼意見相左**。期望值必須來自獨立的真相來源 ——
> 一個已知good的字面值、一個算過的例子、**規格**。

具體地說:驗「總金額 = Σ(單價 × 數量)」那條契約時,期望值要寫規格算過的那個
字面值(規格 S2 已經算出 TWD 568.50),**不准在測試裡再跑一次 Σ(單價 × 數量)
去算期望值** —— 那樣不管實作怎麼寫它都會綠。

同理:不准用實作的常數、列舉、格式化函式去組期望值。期望值是抄規格的,
不是算出來的。

---

## 七、不得開工的部分

以下區塊在需求方裁決前**不得實作**(規格〈不得開工的部分〉逐條):

1. **訂單的重複送出/冪等處理**(阻斷 S13)——不得加上任何去重、冪等鍵、
   防連點機制,也不得刻意允許重複。這一塊留空。
2. **商品可售性檢查**(阻斷 Q18 對應契約)——不得加入下架檢查、庫存檢查
   或缺貨拒絕。
3. **C8 的聚合邊界最終形態**——可依 ASSUMPTIONS 的權宜作法先跑,但不得據此
   新增聚合根或搬動邊界。

把洞留成洞。**不要因為「順手做一下比較完整」就填它們。**
規格〈明確不在範圍〉那一整節同樣不做:分頁、搜尋、篩選、排序、折扣、運費、
收款、通知、其他訂單狀態、修改與取消、收件資訊、權限分級、多幣別。

---

## 八、歧義自己決定,記進 ASSUMPTIONS.md

規格沒寫清楚的地方,**你自己決定,不要問人**,然後逐條記進工作目錄根目錄的
`ASSUMPTIONS.md`。一條一列,三格:

| 自決內容 | 依據 | 待確認點 |

「依據」要寫本文(為什麼這樣決定),不要寫「見某某節」。
「待確認點」要寫這個決定猜錯的話會怎樣。

第七節那三條**不是**歧義,是明令留白 —— 不准用「我自決了」把它們填掉。

---

## 九、其他規則

- 只做 `spec/SPEC.md` 裡實際寫出來的東西,不要自己加需求。
- 不要讀這個目錄以外的東西,也沒有參考實作可抄。
- 註解與 `ASSUMPTIONS.md` 用繁體中文;class 名、欄位名照規格與驗收測試裡的英文名。
- 收工前跑一次 `./gradlew test`,把結果貼出來。

開始吧。從 S1 那一條開始。
EOF

# ---- 4b. 這一跑吃了什麼 + 閘門有沒有跳:run-meta.json(票 21)---------------
# 形狀照 run_act2.sh。這支原本沒有 run-meta.json;骨架的 blob 已在 harness/skeleton-blobs.txt,
# 這裡只記 model / spec / 骨架 / 閘門。
cat > "$WORK_ABS/run-meta.json" <<META
{
  "model": "$MODEL",
  "spec": "$SPEC_ABS",
  "skeleton": "$SKEL_ABS",
  "gate_skipped": $GATE_SKIPPED,
  "gate_skip_reason": $GATE_REASON_JSON
}
META

# ---- 5. 跑(或 dry-run)---------------------------------------------------
if [ "$DRY" = "1" ]; then
  echo "dry-run:工作目錄組好了,沒有呼叫 claude"
  echo "  spec      : $WORK_ABS/spec/SPEC.md"
  echo "  prompt    : $WORK_ABS/prompt.txt"
  echo "  gradle 注入: $WORK_ABS/harness/inner-tests.gradle"
  echo "  雜湊基線  : $WORK_ABS/harness/protected-baseline.txt"
  echo "  骨架 blob : $WORK_ABS/harness/skeleton-blobs.txt"
  echo "  run-meta  : $WORK_ABS/run-meta.json"
  echo "  model     : $MODEL(未使用)"
  exit 0
fi

cd "$WORK_ABS" || exit 90
env -i HOME="$HOME" PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/bin:/bin" \
    USER="$USER" SHELL=/bin/bash TERM=dumb LANG=en_US.UTF-8 WORK="$WORK_ABS" MODEL="$MODEL" \
  bash -c '
    cd "$WORK"
    claude -p "$(cat prompt.txt)" --model "$MODEL" --safe-mode \
      --permission-mode bypassPermissions --output-format json
  ' > "$WORK_ABS/result.json" 2> "$WORK_ABS/stderr.log"
rc=$?

# ---- 6. 竄改查驗(擋不住,但查得出來)--------------------------------------
hash_protected > "$WORK_ABS/harness/protected-after.txt"
if diff -u "$WORK_ABS/harness/protected-baseline.txt" \
           "$WORK_ABS/harness/protected-after.txt" > "$WORK_ABS/tamper-check.txt" 2>&1; then
  echo "受保護檔沒有被動過" >> "$WORK_ABS/tamper-check.txt"
  echo "ok: 受保護檔沒有被動過"
else
  echo "⚠️ 受保護檔被改過 —— 這一跑作廢,細節見 $WORK_ABS/tamper-check.txt" >&2
fi

if find "$WORK_ABS/src/main/java/com/shop" -name '*.java' ! -name 'Application.java' | grep -q .; then
  echo "ok: 有實作落地,跑 ./gradlew test 看完成的定義"
else
  echo "rc=$rc:沒有任何實作 class 落地"
fi
