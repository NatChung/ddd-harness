# DDD × AI agent harness 開源專案調查(2026-08-25)

調查對象:GitHub 上自稱「DDD / spec-driven / harness engineering」的專案,跟本 repo 的五幕管線比。
每條主張都標 **驗過**(親眼在原始碼/腳本裡看到)、**宣稱**(只有 README 說)、**轉述**(拿不到一手來源,靠第三方)。
負面主張(「他們沒有」)一律限定在**已讀的檔案範圍**內——fspec 有 171 支 command,本次讀了其中約 15 支。

比較用的詞彙照 `CONTEXT.md`:負面情境 / 代理編碼 / wire shape / 可滿足性 / 指名測試 / 不適用 / 對譯檢查 / 骨架 / 內圈測試 / 恆真。

---

## 1. 一句話結論

1. **有沒有人做得比我們好?** 在「驗收怎麼來、驗收健不健康」這一段沒有;在「流程順序由機器擋、情境→測試→實作有可追溯的落點、對 harness 自己的規約也上 lint」這三段有——fspec 與 Agentheim 各自把這幾件事機械化了,我們還是手動按順序跑腳本。
2. **我們這種方式好不好?** 三個主要 harness 都是**同一個 agent 寫 spec、寫測試、寫 code**,再用事後手段(LLM 驗證員 / mtime 時序 / mutation 門檻)補假驗收的洞;我們把「測試從結構化 spec 生成」放在構造上,假驗收在那一道縫是被結構擋掉的。反過來,他們把**順序**機械化了(狀態機拒絕跳幕),我們的五幕之間什麼都不擋。
3. **有沒有別的方式?** 有三種形狀跟五幕根本不同:(a) 限制 agent 的**動作空間**而不是驗它的**產物**(statewright 每階段工具白名單、Harmonist stop hook 拒絕結束回合);(b) 用**隔離、不同模型、量過命中率**的 LLM 驗證員當閘門(Agentheim);(c) 用**架構分數對基線**當連續感測器而非 pass/fail 規則(sentrux)。

---

## 2. 對照表

| repo | 迴圈形狀 | spec 形式 | 測試誰生 | 機械檢查(摘要,細節見 §3) | agent 隔離 | 驗過 / 宣稱 |
|---|---|---|---|---|---|---|
| **sengac/fspec** | Kanban work unit 走 `backlog→specifying→testing→implementing→validating→done` 狀態機;每個 work unit 一個 agent | Gherkin `.feature`(結構化)+ `work-units.json`(Example Mapping:rules / examples / questions / assumptions)+ `foundation.json` | **同一個 agent** 寫 Gherkin、寫測試、寫 code | 狀態轉移守衛、轉移前置條件、時序(mtime)、prefill 佔位符、`@step` 註解對譯、coverage sidecar、Gherkin byte-parity、tag 註冊表、pre-transition hooks | 無角色隔離;可選 git worktree | 驗過(`update_work_unit_status.rs` 全文、`step_docstrings.rs`、`check.rs`、`audit_coverage.rs`、`validate_*.rs`) |
| **heimeshoff/Agentheim** | brainstorm→vision;modeling→每 BC 的 task 檔;work→worker(sonnet,worktree,TDD)→**verifier**(opus,fresh context,唯讀)→squash-merge | markdown task 檔,`- [ ]` 散文 acceptance criteria;BC README 的 Ubiquitous Language 節 | **worker agent** 自己寫(TDD) | `lib/*.mjs` 的 live-tree lint、`task-lifecycle.mjs` 合法移動 + fail-closed `depends_on`、derived-artifact-guard;其餘 8 項檢查是 **LLM 判斷**(verifier) | worker 與 verifier **不同模型、不同 context、verifier 無 Write/Edit** | 驗過(verifier.md、worker.md、兩個 SKILL、五條 ADR、`lib/` 7 支、eval 報告);「100% vs 54.8%」是 README 宣稱,未驗 |
| **studioKjm/ai-harness-template** | `/interview`(模糊度分數)→`/seed`(不可變 YAML)→`/trd`→`/decompose`→`/run`→`/evaluate`(三階)→`/evolve` | YAML seed spec:goal / constraints / acceptance_criteria(id, verification, priority)/ ontology / architecture(3-tier) | **同一個 agent**;Pro 有 `test-scaffold`(產 `expect(true).toBe(false)` 骨架);Pair Mode 的 Test Designer 在 worktree 裡不看 `src/` | 12 支 bash gate(boundaries / layers / secrets / security / structure / spec / deps / mutation / complexity / performance / ai-antipatterns / surgical-changes)+ 方法論 gate(test-first / context-boundary / scenario-coverage / spec-drift) | Pair Mode Test Designer 隔離(**宣稱**);`check-security-ai` 開新 Claude session(驗過腳本存在,未讀本體) | 驗過 11 支 gate 腳本、CI workflow、pre-commit;Pro 三支 Python |
| **unrealandychan/clean-code-skill** | 沒有迴圈;是 prompt adapter + lint config 包 | 無 spec;rules.md 是給 AI reviewer 的規則 | 不管 | ESLint `import/no-restricted-paths`(domain 不得 import infra,**warn** 級)、`import/no-cycle`(error)、golangci `depguard`、pre-commit、commitlint;DDD 規則(ubiquitous-language / bounded-context-violation / aggregate-integrity-bypass)**全是 AI review 散文** | 無 | 驗過 lint 設定三份 |
| lopopolo/harness-engineering | 文集,無 code 檢查;有 `sources/scripts/validate_manifest.py`(驗自己的來源清單) | — | — | — | — | 驗過 README + 4 章 + 1 playbook |
| statewright(awesome 清單追) | 狀態機決定每階段能用哪些工具 | 無 | — | 每階段工具白名單硬擋、bash 判別、編輯行數上限、指令前綴白名單、guard 條件轉移 | 用 hook 攔工具呼叫 | **宣稱**(只讀 README) |
| Harmonist(同上) | stop hook 拒絕結束回合直到 reviewer 跑過、memory 更新 | 無 | — | stop gate、`MANIFEST.sha256` 供應鏈、post-install anchor 偵測 gate 被削弱、PROTOCOL-SKIP 濫用率門檻、memory schema 驗證 | reviewer subagent 唯讀 | **宣稱**(只讀 README) |
| sentrux(同上) | 掃→分數→agent 改→重掃 | `.sentrux/rules.toml`(layers / boundaries / max_cycles) | — | `gate --save` / `gate` 對基線比退化;`check` 規則;tree-sitter 52 語言(AST,不是 grep) | MCP `session_start` / `session_end` | **宣稱**(只讀 README) |
| **本 repo** | 五幕:訪談→落檔→生成→實作→review | 散文 SPEC-draft → `acceptance.yaml` → `spec.db`(SQLite,schema 有 CHECK/FK/TRIGGER) | **生成器**(`gen_acceptance.py` / `gen_archunit.py`),agent 只寫內圈測試 | relay_ledger、landing_check、schema 約束、spec_store 跨列不變式、provenance_check、contract_triage、glossary_check、verify_generated、acceptance_gwt(空骨架全紅 / 可滿足 / 逐條可紅)、vacuous_tests、package_landing_check、雜湊防竄改、生成的 ArchUnit | bare dir;答案卷不進工作目錄;內圈用 source set 結構隔離 | 見 `PIPELINE.md` 每段的「驗過沒有」 |

---

## 3. 他們有、我們沒有的機械檢查(20 條)

判準:機器判定、CI 可跑、不靠 agent 自律。LLM 判斷(Agentheim verifier、aht `/evaluate` Stage 2/3、`check-security-ai`)**不列在這裡**,放 §5。
「我們沒有」= 在 `PIPELINE.md` 列的 13 支檢查與 `tools/harness/` 裡沒有對應物。

### fspec(全部驗過,原始碼 `rust/fspec-core/src/commands/`)

1. **狀態機轉移守衛,不可跳幕。** `allowed_transitions(from)` 是硬編碼的合法轉移表;`backlog→testing` 直接回 `Err("Must move to 'specifying' state first. ACDD requires specification before testing.")`。
   出處:`update_work_unit_status.rs` L45–66(表)、L149–171(拒絕訊息)。
   我們:五幕是五支腳本,沒有任何東西擋「跳過 `acceptance_gwt` 直接跑 `run_act4.sh`」。

2. **轉移前置條件(存在性檢查,不看內容)。** `specifying→testing` 要:`rules>0 && examples>0`(Example Mapping)、`architectureNotes>0`、附件裡有 `ast-research` 檔、沒有未答的 question、至少一個情境帶 `@<id>` tag、bug 型必須連到既有 feature。`implementing→validating` 要每個 scenario 都有 impl mapping。
   出處:L201–259(轉移分支)、L674–745(`perform_review_validation`、`check_scenarios_exist`)、L751–(`check_coverage_completeness`)。
   ⚠️ 全是**有沒有**的檢查:`rules` 陣列非空就過,內容是什麼不管。跟我們的 `contract_triage`「有指名測試 ≠ 由誰強制」是同一個上限。

3. **時序檢查:檔案 mtime 必須晚於進入該狀態的時間。** `specifying→testing` 比 feature 檔 mtime 對 `stateHistory` 裡第一次進 `specifying` 的 timestamp;`testing→implementing` 比測試檔對進 `testing` 的時間。早於就拒絕,印出 gap 分鐘數。目的寫得很白:擋「先把事做完,再把狀態一路走過去當表演」(`fspec_workflow_guidance.rs` L507:*retroactive state walking … as theater*)。
   出處:`update_work_unit_status.rs` L974–1060(`check_temporal_ordering`)。
   上限(驗過):比的是 **mtime 不是 git**,`touch` 就過;有 `skipTemporalValidation` 逃生口。
   我們:`run_act4.sh` 的雜湊只查「受保護檔有沒有被改」,不查「測試是不是在實作之前就存在」——那條是靠幕三→幕四的**構造順序**保證的,沒有機械檢查。

4. **prefill 佔位符擋所有前進轉移。** 連到的 feature 檔若含 `[role]` / `[action]` / `[benefit]` / `[precondition]` / `[expected outcome]` / `[scenario name]` / `TODO:` 任一字串,所有非 `blocked` 的轉移都拒絕,並印「DO NOT use Write or Edit tools to replace prefill directly」。
   出處:L189–192、L581–603(`detect_prefill`)、L634–667(`check_prefill`)。
   我們:`spec_store.py` 匯入時擋不擋空字串 / 佔位符**沒驗過**;沒有這一支。

5. **`@step` 註解 ↔ Gherkin step 逐條對譯,且每個 feature 只准連一個測試檔。** 進 `implementing` / `validating` 時,對每個帶 `@<id>` 的 feature:coverage 檔必須存在、必須是合法 JSON、至少一個 test mapping、**最多一個**不同的測試檔(1:1)、每個 scenario 的每一步都要在測試檔裡找到對應的 `// @step …` 註解(相似度匹配:Jaro-Winkler / token-set / trigram / Jaccard 混合)。
   出處:`update_work_unit_status/step_docstrings.rs` L1–22(規則列表)、L46–;`fspec_workflow_guidance.rs` L332–355(規則散文)。
   我們:測試是生成的,對譯**由構造保證**,所以不需要;但**內圈測試**沒有任何「對到哪一條驗收」的落點——票 13 開著的洞。

6. **coverage sidecar:scenario → 測試檔+行號 → 實作檔+行號,並稽核檔案存在。** `link-coverage` 寫 `<feature>.feature.coverage`;`audit-coverage` 逐條檢查引用的測試檔與實作檔是否還在磁碟上(exit 1 列出缺的);`generate-coverage` 重生 sidecar 時若情境集合漂了就標 `updated`,同步就 `skipped`(逐位元組不動)。`done` 轉移要求 coverage 完整(否則降為 warning——見 §4 第 11 條)。
   出處:`link_coverage.rs` L1–22、`audit_coverage.rs` L1–34、L119–149;`generate_coverage.rs` L1–30。
   我們:規格→驗收有(生成),**驗收→實作 class** 沒有任何可追溯的落點。

7. **相依守衛:`blockedBy` 未 `done` 不准進任何 active 狀態。**
   出處:L175–187、L466–478(`collect_active_blockers`)。
   我們:票的 blocked 關係寫在散文 Status 裡,沒有東西讀它。

8. **Gherkin 格式 byte-parity + tag 註冊表。** `fspec check` 對每個 feature 檔:parse → 用 AST formatter 重新序列化 → 逐位元組比,不同就 FAIL;每個 tag 必須在 `spec/tags.json` 註冊、放對類別。
   出處:`check.rs` L1–46(模組文件)、L156–182。
   我們:`verify_generated.py` 是同一招,但對象是生成物;spec yaml 本身沒有 canonical-format 檢查。

9. **轉移前的 blocking hook(使用者自寫腳本)。** `run_pre_hooks` 在轉移前跑 `spec/fspec-hooks.json` 登記的腳本,非零就擋。範例 `validate-feature.sh` 從 stdin 讀 `workUnitId`,查 `spec/features/<id>.feature` 存不存在。
   出處:L295–296;`examples/hooks/validate-feature.sh` 全文。

### Agentheim(驗過,`lib/`)

10. **task-lifecycle mover:合法移動集合 + fail-closed `depends_on` + status↔資料夾一致 + mtime 樂觀前提。** `LEGAL_MOVES.skill = {backlog->todo, todo->doing, doing->done}`,倒退與跳格非法;`depends_on` 裡任何一個 id 在四個資料夾都找不到就算**未滿足**(ADR-0038 Ruling A,明確推翻 SKILL 散文原本的「找不到視為滿足但警告」);移動時**同時**改資料夾與 frontmatter `status`,不准只改一半;磁碟狀態跟預期不符就拒絕且不動任何東西。
   出處:`lib/task-lifecycle.mjs` L1–40(檔頭)、L412–415;ADR-0038 L33–51。
   我們:票的 `Status` 是散文,`CLAUDE.md` 自己承認「漂得很兇」;沒有 mover。

11. **derived-artifact-guard:在 conductor 的 `git add` 那一格過濾宣告的 FILE_LIST。** 不掃樹、不跑 git,純字串:任何落在 `dashboard/dist/` 前綴下的路徑拒絕 stage。設計理由寫得很準:「建置產物只有一條路能逃出 worktree 到 main——就是那次 enumerated stage;擋那一格就夠」。
   出處:`lib/derived-artifact-guard.mjs` L1–24、L153–160。
   我們:`verify_generated` 方向相反(生成物有沒有被手改),沒有「不該 commit 的東西不准進 stage」。

12. **對 harness 自己的規約與票上 lint(`node --test lib/test/*.test.mjs`)。** 七支:`human-eye-criteria`(全是 `[human-eye]` 的票必須帶「builder-eye only」註記)、`spike-stop-loss`(`type: spike` 的票必須含 stop-loss 子句)、`doctrine-line-pointer`(`skills/`、`agents/`、`references/` 裡禁止 `file.md:123` 這種行號指標,只准 greppable 錨點)、`index-entry-length`、`id-grammar`、`agent-spawn-namespace`、`duplicate-id-check`。全部 stdlib、side-effect-free、loss-tolerant(讀不到就不標),前三支有 `ADOPTION_DATE` 祖父條款。
   出處:`lib/human-eye-criteria.mjs` L1–61、`lib/spike-stop-loss.mjs` L1–70、`lib/doctrine-line-pointer.mjs` L1–60(三支各讀了檔頭約 60 行——規則、正規式、祖父條款都在檔頭;掃描迴圈本體未讀。其餘四支只讀檔名與 ADR-0059 L88–115 的描述);ADR-0059 §「Self-hosting-only enforcement scope」明說**這些 lint 只在 Agentheim 自己的 repo 跑,消費者專案拿不到**。
   我們:`CLAUDE.md` 有一批對票與文件的規約(Status 前六個詞、`NN-PREDICTION.md` 要在跑之前寫、run 目錄被票引用就不能刪),**一條都沒有 lint**。

### ai-harness-template(驗過,bash)

13. **check-test-first:git 歷史裡 source 檔首次 commit 不得早於對應測試檔。** 從 staged 檔推對應測試檔(語言慣例:`foo.test.ts`、`tests/test_foo.py`、`FooTest.java`…),比兩者 `--diff-filter=A` 的 commit timestamp;測試不在 git 裡就算違規;commit message 以 `[refactor]` / `[chore]` 等前綴開頭可豁免;找不到配對只警告不擋。
   出處:`methodologies/tdd-strict/gates/check-test-first.sh` L146–208。
   比 fspec 第 3 條強:用 git 不用 mtime。上限:配對靠命名慣例。

14. **check-surgical-changes:一次 commit 變更檔數上限(預設 15)。** Karpathy 的「surgical changes」機械代理。
   出處:`gates/check-surgical-changes.sh` L32–57。
   我們:scope discipline 完全沒有機械代理;Agentheim 的 check 3 是 LLM。

15. **check-mutation 門檻式閘門。** mutmut / Stryker 分數 < 60% 就 exit 1。
   出處:`gates/check-mutation.sh` L28、L99–109。
   我們的 `vacuous_tests` 也跑 PIT,但**刻意不當判決**(交分診佇列)。這條算「形狀不同」,列出來是因為門檻閘門是 CI 可擋的,我們沒有。

16. **check-secrets / check-deps / check-security(不是 DDD 主題)。** 35+ 秘密 pattern、`npm/pip audit`、semgrep/bandit。存在驗過(`gates/` 目錄、`pre-commit-gate.sh` L36–42、CI workflow),**腳本本體未讀**。
   我們:沒有任何安全類掃描。列出來是完整性,不是建議採用。

### 只有 README 的三個(宣稱)

17. **Harmonist:stop hook 拒絕結束回合 + PROTOCOL-SKIP 濫用率門檻 + 供應鏈雜湊。** 若 session 動了檔案,`stop` hook 檢查:至少一個 `category: review` agent 被呼叫、`qa-verifier` 被呼叫、`session-handoff.md` 更新過;不滿足就回 `followup_message` 不讓回合結束,`loop_limit: 3`。`PROTOCOL-SKIP: <reason>` 可跳過,但跳過率 > 25%(至少 5 次)下個 session 開頭警告。`MANIFEST.sha256` 驗每個 agent 定義檔;`.cursor/pack-manifest.json` 在安裝後記雜湊,`verify_integration.py` 抓「有人把 `gate-stop.sh` 改弱」。`require_affected_tests: true` 時 stop gate 要求受影響的測試跑過(用自己的 repomap 算 `affected`)。
   出處:README §「Mechanical enforcement」「Supply-chain integrity」「Local repo map」。**未讀 hook 原始碼。**
   我們:`run_act4.sh` 的雜湊是**事後查得出**(`tamper-check.txt`),Harmonist 是**事前拒絕**;「不適用 / 跳過的比率」我們沒有統計。

18. **statewright:每階段工具白名單硬擋。** `planning` 只給 Read/Grep/Glob,`implementing` 給 Edit/Write 但 `max_edit_lines`、`max_files_per_state`,`testing` 只准 `allowed_commands` 前綴(`pytest`、`cargo test`);Bash 開著時仍擋 `echo > file`、`sed -i`、`python`;轉移可帶 guard(`test_result eq pass`)。
   出處:README §「Guardrails」「Define your own workflows」。
   我們:幕四靠 gradle source set 結構 + 雜湊,agent 的工具全開。

19. **sentrux:架構分數對基線比退化。** `gate --save` 存基線,`gate` 重掃比較,退化就 exit 1;`rules.toml` 定 `max_cycles = 0`、layer order、boundaries;52 語言走 tree-sitter(AST)。
   出處:README §「Quick Start」「Rules engine」。
   我們:ArchUnit 是規則式 pass/fail,沒有「比上一跑退步了多少」。

### OpenAI(轉述,原文 403)

20. **docs/ 當 system of record,由 linter 驗連結與結構;linter 錯誤訊息寫給 agent 讀。** 轉述來源:alexlavaee 部落格(無逐字引用,明說是 paraphrase)、Martin Fowler/Böckeler 文(列出 deterministic 機制清單:type checker、linter、ArchUnit 類結構測試、coverage、mutation testing、pre-commit、custom linter、dependency scanner、dead code)、lopopolo 的 text-fragment 錨點(`openai.com/index/harness-engineering/#:~:text=we%20made%20the%20app%20bootable%20per%20git%20worktree`、`…Review%20comments%2C%20refactoring%20pull%20requests…captured%20as%20documentation%20updates`、`…Codex%20replicates%20patterns%20that%20already%20exist…`)。
   我們:`PIPELINE.md` / `CLAUDE.md` / `CONTEXT.md` 之間的一致性靠人;`CLAUDE.md` 自己列了一串「兩份散文講同一條規則會漂」。

### 不列入的等價物(避免灌水)

- aht `check-boundaries` / `check-layers` / ddd-lite `check-context-boundary`、clean-code-skill 的 `no-restricted-paths` / `depguard`:全是 **import 字串 grep**(`check-layers.sh` L116 `grep -rn "$pattern"`,靠目錄名猜層),我們的 ArchUnit 是 AST 級且從 spec 生成——不是缺口。
- Agentheim ADR-0062「runner-first:第一個測試任務要故意弄壞一個測試證明 runner 會紅」:我們的「空骨架全紅」順便證明了 runner 會報紅——已涵蓋。
- fspec `compare-implementations`:`namingConventionDifferences` **永遠回空陣列**(`compare_implementations.rs` L16「TS leaves it as a TODO」)——是個 stub,不算檢查。

---

## 4. 我們有、他們沒有的(14 條)

「他們沒有」限定在 §2 表列的已讀檔案內。

1. **空骨架全紅(非恆真證明)。** fspec 散文寫「Tests MUST FAIL at this point (red phase)」(`fspec_workflow_guidance.rs` L368),但在 `update_work_unit_status.rs` 全文裡**沒有任何守衛去跑測試確認它是紅的**;Agentheim TDD skill 寫「confirm it fails for the right reason」(L28)是給 worker 的散文,verifier check 1 問「would fail if production code absent」是 LLM 判斷;aht `test-scaffold` 產的骨架是 `expect(true).toBe(false)`(`scaffold.py` L198),紅是紅,但那是佔位符不是驗收。
2. **可滿足性(一份參考實作能讓驗收全綠)。** 三個 repo 都沒有「驗收本身可能是綠的」這條證明。
3. **逐條可紅(`BREAKS` 一次弄壞一條,對應情境單獨變紅)。** 最近的親戚是 mutation testing(aht 第 15 條、我們的 PIT),但那是對實作變異,不是對規格語意逐條驗。
4. **代理編碼是規格層的欄位(`proxy_for`),且生成到獨立的 `OrderProxyAcceptanceTest` class。** Agentheim ADR-0061 的 `[human-eye]` 是最近的親戚(把「機器判不了的條文」標出來、不准拿代理指標冒充),但它標的是**人眼**類,我們標的是「fixture 不含它宣稱的動作」——兩者都在做「不准把不能驗的當成驗過」,對象不同。
5. **provenance_check(宣稱出自需求方的具體值,逐字稿裡真的有嗎)。** Agentheim 的 `research-reviewer` 對研究報告做「checkable claims 對一手來源」——是親戚,但對象是研究不是 spec,而且是 LLM。
6. **relay_ledger + landing_check(訪談每輪答案都轉交、每題都有落點)。** aht `/interview` 有模糊度分數(Pro 的 `ambiguity.py`,權重是 LLM 給的),沒有「這題有沒有記下來」的檢查。
7. **spec 存進 SQLite,schema 層 CHECK/FK/TRIGGER + 跨列不變式(總額 = Σ 數量×單價;拒絕情境的客人不得借用成功情境的)。** fspec 有 JSON schema 驗 `foundation.json` 的形狀(`validate_foundation_schema.rs`,未讀本體)與 `validate_work_units.rs` 的結構一致性(parent/child 互指、status↔states 陣列),都是**形狀**不是**領域不變式**;aht `check-spec.sh` 是 grep 欄位存不存在。
8. **glossary_check(詞彙表 ↔ 對外欄位名的機械對譯)。** Agentheim check 4「新識別字對 BC README 的 UL 節」是 verifier 的 LLM 判斷;clean-code-skill 的 `ubiquitous-language` 是給 AI reviewer 的規則;fspec 的 tag 註冊表是機械的,但管的是 tag 不是領域詞。
9. **contract_triage(「有指名測試」與「由誰強制」分兩欄印、不合併計數)。** 沒有對應物。
10. **驗收由生成器產、agent 拿不到生成器,`verify_generated` 逐位元組比重生。** 三個 harness 的測試都是 agent 寫的。fspec 的 `generate-coverage` 有「同步就 skipped 不動位元組」,Agentheim 有 derived-artifact-guard,都是親戚,但沒有「驗收測試不是 agent 寫的」這件事。
11. **「不適用」是獨立離開碼 3,不折進「通過」。** 驗過三個反例:
    - fspec `check.rs` L87–95:`spec/features` 沒檔案 → `{success: true, message: "No feature files found"}`,CLI exit 0。
    - aht `gates/check-spec.sh` L32–36:沒有 `seeds/` 目錄 → `exit 0`,註解寫「Not a hard failure — spec is optional」;ddd-lite `check-context-boundary.sh` L16–17、bdd `check-scenario-coverage.sh` L13–15 同款。
    - aht `methodologies/living-spec/gates/check-spec-drift.sh` L88–98:整支跑完**永遠 `exit 0`**,註解逐字:「v0.1: best-effort scan only. Don't actually emit warnings yet — too noisy.」——而 `living-spec/manifest.yaml`(未讀,依 ddd-lite / bdd 的 manifest 形狀推斷)對外登記它是 gate。這是別人 repo 裡活生生的「做了 ≠ 接上了」。
    - fspec `check_coverage_completeness` 對 `done` 轉移:coverage 檔不存在 → **warning 不擋**(L790–800「Coverage tracking is optional」),但對 `validating` 轉移是硬擋——同一支函式兩種嚴格度,靠一個 bool 切。
12. **vacuous_tests 的支配關係分診(分不出「恆真」與「碰不到」時交佇列不下判決)。** aht 的 mutation 是門檻判決。
13. **ArchUnit 從 spec 的架構規則生成。** 其他人的架構規則全是手寫設定檔(`boundaries.yaml`、`.eslintrc`、`rules.toml`)。
14. **`NN-PREDICTION.md` 在跑之前寫、跑完 `NN-RESULT.md` 對答案。** Agentheim 的 verifier-catch-rate eval 有 `expected.json`(每個 fixture 的預期判決),是同一個念頭,但只用在量 verifier,沒有用在每一次 harness 改動上。

---

## 5. 根本不同的做法

### (a) 限制動作空間,不驗產物 — statewright、Harmonist、fspec 狀態機(部分)

五幕驗的是**產物**(spec 落不落得了檔、測試紅不紅、生成物有沒有被改)。這一派驗的是**過程**:agent 在這個階段能不能碰這個工具、這個回合能不能結束、這個狀態能不能轉。statewright 的說法是「Agents are suggestions, states are laws」;Harmonist 的是「it's a state machine on disk」。
跟我們最近的接點是幕四的結構隔離——但我們是「內圈測試住別的 source set 所以不算進全綠」,他們是「testing 階段 Bash 只准跑 `pytest`」。
只有 fspec 的部分是驗過的(狀態機在 Rust 裡);statewright / Harmonist 是宣稱。

### (b) 隔離、去相關、量過命中率的 LLM 驗證員 — Agentheim

verifier 不是機械檢查,但它的**周邊**是結構性的:唯讀工具、不同模型(worker sonnet / verifier opus,ADR-0031 說理由是去相關不是判斷力)、拿不到 worker 的推理、每次判斷獨立(除了 check 1b 的一個窄例外)。
真正跟我們相關的是**他們量了這把儀器**:`evals/verifier-catch-rate/` 16 個 fixture 各埋一個已知缺陷 + `expected.json`,k=3 真跑,60 次 spawn;量到 opus 對 `missing-adr-borderline` 0/6 漏掉、sonnet 6/6 抓到;追到是 check 6 **措辭的洞**不是模型差,改措辭後 opus 3/3(`verifier-catch-rate-eval-2026-07-04.md` L359–408)。這跟我們幕五「洞 → 搬階 → 改 harness → 重跑證明它掉不了」是同一個迴圈,而且他們**有 fixture 語料可以重跑**,我們只有歷史 run。
ADR-0059「mechanize-or-drop」是另一條可借的規約:建立慣例的任務**要嘛同 task 交 lint,要嘛在票裡寫明「prose-only, unenforced」**——把「沒機械化」變成記錄在案的決定而不是意外。ADR 自己承認這條 gate 是 LLM 判斷。

### (c) 連續感測器對基線 — sentrux

不是「這條規則過不過」,是「五個指標算成 0–10000 一個分數,session 前存基線、session 後比,退了就擋」。宣稱。跟我們的 ArchUnit 是互補的:規則擋已知的違反,分數抓沒寫成規則的退化。

### (d) 把 repo 本身當 prompt,回饋往 lint 搬 — lopopolo / OpenAI(轉述)

lopopolo 對「harness 該有哪些檢查」的定義不是清單,是**四條判準**:
- **證據要配得上主張**(`docs/proof/README.md` L37–59 的 claim↔evidence 對照表:瀏覽器行為要真瀏覽器旅程,生成內容要 source-to-output 完整比對,部署要 post-deploy health;「Unit tests, type checks, lints, and builds establish important internal properties」——只證內部性質)。
- **分清「證明宣稱行為的檢查」與「只證內部一致的檢查」**(`playbooks/repository-review.md` L32–33)。
- **文件把強制程度講過頭就是不合格**(同檔 L251–262 readiness blockers:「documentation that materially overstates enforced guarantees」)。
- **steering → 文件 → reviewer → lint/test 的升階順序**(`docs/feedback/README.md` L101–128 那張表:「lint, test, or policy check — a deterministic invariant should block recurrence」),加一條「if it matters, it belongs in a verifier owned by the repo」(引 hyperbo.la)。
這四條跟本 repo 的「做了 ≠ 接上了 ≠ 驗過了」是同一件事的另一種寫法;lopopolo 的 repo 自己沒有 code 檢查(只有 `sources/scripts/validate_manifest.py` 驗來源清單)。

### (e) 對 harness 自己的不變式做形式驗證 — fspec Alloy

`docs/FORMAL_VERIFICATION.md`:對 compaction / token tracker / DAG 三個子系統寫 Alloy 模型,bounded model check,再用 proptest 鏡射到實作(「Alloy proves the model, proptest proves impl matches model」)。對象是 fspec 自己的 Rust,不是使用者專案。跟我們最近的是 `schema.sql` 的跨列不變式——但我們是在 SQLite 裡擋,不是證明。

---

## 6. 判斷(標明是判斷)

**判斷 1:驗收這一段我們領先,而且是結構性領先。** 三個主要 harness 都讓同一個 agent 寫 spec、寫測試、寫 code,再事後補:fspec 用 mtime 時序 + `@step` 對譯,Agentheim 用 LLM verifier,aht 用 mutation 門檻。我們把測試從結構化 spec **生成**,agent 拿不到生成器——假驗收在那道縫是被構造擋掉的,不是被抓的。加上「空骨架全紅 / 可滿足 / 逐條可紅」三態,沒有一個對照組有等價物。這一段不用改方向。

**判斷 2:順序這一段我們落後,而且落後的是最便宜的那種機械化。** fspec 的 `allowed_transitions` 表 20 行,Agentheim 的 `LEGAL_MOVES` 3 行——都在拒絕「跳幕」。我們的 `PIPELINE.md` 用文字說「幕三之後才幕四」,`CLAUDE.md` 用文字說「動 harness 之前先寫 PREDICTION」,沒有任何東西擋。這正是 `MISSION.md` 說的「不隨換模型漂移」最容易漂的地方:順序靠自律。候選做法(判斷,未驗):一支 `run_pipeline.py`,幕 N 的檢查離開碼不是 0 就不解鎖幕 N+1 的 runner;`NN-RESULT.md` 存在而 `NN-PREDICTION.md` 的 mtime / git 首次 commit 不早於對應 run 目錄就標紅。

**判斷 3:對 harness 自己的規約上 lint,是 Agentheim 給的最直接可抄的東西。** `CLAUDE.md` 列了至少四條可機械化的規約(Status 開頭詞、票檔名格式、run 目錄被票引用就不能刪、PREDICTION 先於 RESULT),全靠讀 `CLAUDE.md` 的 agent 自律。ADR-0059 的做法是:每條慣例要嘛交 lint,要嘛在票裡寫「prose-only, unenforced」+ 理由。這個 repo 已經在做後半(每段標「驗過沒有」),缺的是前半。

**判斷 4:「不適用 ≠ 通過」是我們最清楚的差異化,而且有三個對照組的反例可以拿來當教材。** fspec `check` 零檔案 → success、aht 四支 gate 沒東西可查 → exit 0、aht `check-spec-drift` 整支是 no-op 但登記為 gate——`CONTEXT.md` 的「守衛沒有壞掉,是不再適用了,而不適用不會有人發現」在別人 repo 裡有實例。適合進第十課或 `learning-records`。

**判斷 5:驗收 → 實作的落點是我們最大的空白。** fspec 的 coverage sidecar(scenario → 測試行 → 實作行,`audit-coverage` 查檔案還在不在)是我們沒有的一整層。票 13(內圈落點)開著,票 01(動詞不夠)卡著 06-B/C——fspec 的做法是讓 agent 自己 `link-coverage`,靠狀態機在 `validating` 擋沒連的。對我們來說,內圈測試的落點可以走同一條:`src/innerTest/` 每支測試檔頭要宣告 `@covers S<n>`,`package_landing_check` 之外多一支 `innertest_landing_check`,沒宣告的印「不適用」而不是通過。(判斷,形狀未定,屬票 13 的範圍。)

**判斷 6:Agentheim 的 verifier eval 方法值得抄,verifier 本身不值得抄。** 我們的 `landing_check` / `provenance_check` 各自對三四份真實 run 驗過,但沒有「埋已知缺陷的 fixture 語料 + expected + k 次重跑」。他們用這個抓到 gate 措辭的洞,而且改完能重跑證明。這是幕五「改了但沒重跑 = 沒閉環」的機械化版本。至於用 LLM 當閘門,跟 `MISSION.md`「對不對這件事不需要人主觀判斷」是相反方向,不建議。

**判斷 7:時序檢查值得做,但用 git 不用 mtime。** fspec 用 mtime(`touch` 就過),aht `check-test-first` 用 git 首次 commit 時間(較穩,但配對靠命名慣例)。我們的場景更簡單:`runs/<date>-act4/` 裡受保護檔的雜湊已經有了,補一條「生成測試檔的 git 首次 commit 早於任何 `src/main` 檔」就是 aht 那支的簡化版。

---

## 7. 沒查到 / 拿不到的

- **OpenAI `harness-engineering` 原文:HTTP 403。** 用三個轉述:alexlavaee 部落格(自己說沒有逐字引用)、Martin Fowler 站 Böckeler 文(有引 OpenAI 一句結論)、lopopolo repo 的 `#:~:text=` 錨點(能證明原文含那幾段字串,但看不到上下文)。lopopolo 附了 `sources/scripts/fetch_openai.py` 給被擋的 agent 用,**沒跑**。
- **lopopolo/harness-engineering:`main` / `master` 都 404,預設分支是 `trunk`。** 已改用 trunk 抓到。
- **Agentheim「Benchmarked at 100% vs. 54.8% on the reference suite」:README 宣稱,`evals/` 目錄存在但沒找對應的數字檔,未驗。**
- **Agentheim `lib/` 七支 lint 只讀了三支的檔頭約 60 行**(human-eye-criteria、spike-stop-loss、doctrine-line-pointer;規則與正規式在檔頭,掃描本體未讀)+ task-lifecycle 檔頭 80 行 + derived-artifact-guard 檔頭 60 行;其餘四支(index-entry-length、id-grammar、agent-spawn-namespace、duplicate-id-check)只有檔名與 ADR-0059 的描述。
- **Agentheim `skills/work/SKILL.md`(104 KB)只讀了標題**;verifier prompt template、squash-merge 流程細節沒讀。
- **fspec 171 支 command 讀了約 15 支**;`validate_foundation_schema.rs`、`validate_hooks.rs`、`validate_tags.rs`、`link_coverage/step.rs`(相似度匹配)沒讀本體。`compare_implementations` 讀了,是 stub。
- **fspec 有沒有機械檢查「測試在 red phase 真的紅」:在 `update_work_unit_status.rs` 全文與 `fspec_workflow_guidance.rs` 的 grep 裡沒找到**;不排除在別支 command 裡。
- **aht `check-secrets.sh` / `check-security.sh` / `check-deps.sh` / `check-structure.sh` / `check-security-ai.sh` 本體未讀**,只驗了存在與被 pre-commit / CI 呼叫;`living-spec/manifest.yaml` 未讀(它登記 `check-spec-drift.sh` 為 gate 這件事是依 ddd-lite / bdd 的 manifest 形狀推斷)。
- **aht Pair Mode「Test Designer 在 worktree 隔離、看不到 src/」:README 宣稱**,`agents/test-designer.md` 未讀。
- **statewright / Harmonist / sentrux:只讀 README**,hook / engine 原始碼沒讀;三個都拉了 tree 但沒進一步用。
- **awesome-harness-engineering 清單裡跟 DDD 直接相關的條目:一條都沒有**(122 條命中裡是 harness / eval / sandbox / memory 類);「DDD × agent」這個交集在該清單裡是空的。
- **未搜 GitHub 全站**——只查了任務指定的 repo 與清單裡挑的三個。

---

## 8. 來源清單

### 一手(原始碼 / 腳本 / 文件,全部經 raw.githubusercontent.com 或 api.github.com 抓取,2026-08-25)

**sengac/fspec (main)**
- `AGENTS.md`
- `docs/FORMAL_VERIFICATION.md`、`docs/TESTING.md`
- `examples/hooks/validate-feature.sh`
- `rust/fspec-core/src/commands/update_work_unit_status.rs`(全文)
- `rust/fspec-core/src/commands/update_work_unit_status/step_docstrings.rs`(L1–80)
- `rust/fspec-core/src/commands/check.rs`、`audit_coverage.rs`、`validate_spec_alignment.rs`、`validate_work_units.rs`、`compare_implementations.rs`(全文)
- `rust/fspec-core/src/commands/generate_coverage.rs`、`link_coverage.rs`(檔頭)
- `rust/tools/src/fspec_workflow_guidance.rs`(grep + L325–375、L505–545)
- tree:`api.github.com/repos/sengac/fspec/git/trees/main?recursive=1`(9,938 項)

**heimeshoff/Agentheim (main)**
- `README.md`
- `agents/verifier.md`、`agents/worker.md`、`agents/orchestrator.md`
- `skills/test-driven-development/SKILL.md`、`skills/verification-before-completion/SKILL.md`、`skills/work/SKILL.md`(僅標題)
- `.agentheim/knowledge/decisions/0036`、`0038`、`0059`、`0061`、`0062`
- `.agentheim/knowledge/verifier-catch-rate-eval-2026-07-04.md`、`evals/verifier-catch-rate/README.md`
- `lib/human-eye-criteria.mjs`、`lib/spike-stop-loss.mjs`、`lib/doctrine-line-pointer.mjs`(L1–60)、`lib/task-lifecycle.mjs`(L1–80)、`lib/derived-artifact-guard.mjs`(L1–60)、`lib/vacuum-guard.mjs`、`lib/vision-conformance.mjs`(L1–60)
- tree(1,306 項)

**studioKjm/ai-harness-template (main)**
- `README.md`(韓文)
- `gates/GATES.md`、`gates/check-boundaries.sh`、`check-layers.sh`、`check-spec.sh`、`check-mutation.sh`、`check-ai-antipatterns.sh`、`check-surgical-changes.sh`
- `methodologies/tdd-strict/gates/check-test-first.sh`、`ddd-lite/gates/check-context-boundary.sh`、`bdd/gates/check-scenario-coverage.sh`、`living-spec/gates/check-spec-drift.sh`
- `methodologies/ddd-lite/manifest.yaml`、`bdd/manifest.yaml`
- `pro/src/harness_pro/drift/monitor.py`、`testing/scaffold.py`、`evaluation/pipeline.py`
- `boundaries/hooks/pre-commit-gate.sh`、`templates/github-actions-gates.yaml`、`feedback/detect-violations.sh`
- tree(361 項)

**unrealandychan/clean-code-skill (main)**
- `README.md`
- `linting/typescript/.eslintrc.json`、`linting/go/.golangci.yml`、`linting/shared/.pre-commit-config.yaml`
- `skills/shared/rules.md`、`harness-rules.md`(僅標題)
- tree(111 項)

**lopopolo/harness-engineering (trunk)**
- `README.md`、`docs/README.md`、`docs/proof/README.md`、`docs/feedback/README.md`、`docs/domain-modeling/README.md`、`playbooks/repository-review.md`
- tree(82 項)

**ai-boost/awesome-harness-engineering (main)**
- `README.md`(238 KB,關鍵字篩 122 條)

**statewright/statewright、GammaLabTechnologies/harmonist、sentrux/sentrux (main)**
- 各自 `README.md`

### 轉述(OpenAI 文章 403)
- https://alexlavaee.me/blog/openai-agent-first-codebase-learnings/(WebFetch 摘要;作者未逐字引用)
- https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html(WebFetch 摘要)
- lopopolo repo 內的 `openai.com/index/harness-engineering/#:~:text=…` 錨點(見 `docs/proof/README.md` L84–85、`docs/feedback/README.md` L41–42、L138–139、`docs/domain-modeling/README.md` L154–155)

### 本 repo
- `tools/harness/PIPELINE.md`、`MISSION.md`、`CONTEXT.md`、`CLAUDE.md`
