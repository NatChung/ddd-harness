# ADR 0007 — 新慣例要嘛交 lint,要嘛寫明「prose-only, unenforced」

## Status

Accepted(2026-08-25)

## Context

這個 repo 反覆出現的失效是「做了 ≠ 接上了 ≠ 驗過了」。`CLAUDE.md` 的〈票怎麼開、怎麼關〉
列了一批規約 —— Status 開頭用六個詞之一、`NN-PREDICTION.md` 要在跑之前寫、run 目錄被票
引用就不能刪、檔名 `NN-kebab-slug.md` —— **一條都沒有東西在守**,而且 `CLAUDE.md` 自己承認
Status「漂得很兇」。同一份文件的票號計數還寫「目前到 18」,實際已到 20。

對照(`docs/research/2026-08-25-harness-survey.md` §3 第 12 條,驗過):Agentheim 的
ADR-0059 訂了一條 repo 規則,每個「建立慣例」的票必須二選一 —— 同票交 lint(live-tree
`node --test`),或在票裡逐字寫「prose-only, unenforced」加理由。三支 lint 都有
`ADOPTION_DATE` 祖父條款,舊資料不追溯。他們的用詞是 **mechanize-or-drop**。

我們已經在做這條規則的後半(`PIPELINE.md` 每段標「驗過沒有」),缺的是前半:
**規約成立的那一刻就決定由誰守**,不是事後再補。

## Decision

1. **任何票、ADR、`CLAUDE.md`、`PIPELINE.md`、runner 註解裡新立的慣例**(命名 / 格式 /
   順序 / 「要先做 X 才能做 Y」這類別人以後要照做的規則),在同一張票裡二選一:
   - 交一條機械檢查:進 `tools/lint/harness_lint.py`(票 22)或 pytest;**或**
   - 在票裡逐字寫 **「prose-only, unenforced」** + 一句為什麼守不了(第 4 階,人讀)。
2. **既有慣例用祖父條款**:lint 只對 `ADOPTION_DATE = 2026-08-25` 之後**首次 commit** 的
   檔案生效(用 git 首次 commit 日期,不用 mtime)。舊票的 `A 半 done` / `resolved` 不追溯改。
3. **「沒東西可查」是不適用,不是通過**:`harness_lint` 沒掃到任何票就離開碼 3,自成一類
   印在最上面(與 `CONTEXT.md` 不適用詞條、ADR 0005 §6 對齊)。
4. 這條 ADR 本身的守法:`harness_lint` 多一條 —— 2026-08-25 之後開的票,內文若含
   「慣例」「規約」「一律」「必須」這類立規的詞,而票裡既沒引用 `harness_lint` 規則名、
   也沒有「prose-only, unenforced」字串,列進分診佇列(**佇列不是判決**;這條抓得到
   「忘了決定」,抓不到「決定錯了」)。

## Consequences

- 票 22 交 `harness_lint.py` 與第一批規則;之後每張票開頭的〈慣例〉一節要嘛指規則名,
  要嘛寫 prose-only。
- `CLAUDE.md`〈票怎麼開、怎麼關〉加一段指向本 ADR。
- **沒驗過的**:第 4 條那個關鍵字偵測的假陽性率。先當佇列,量過再決定要不要升成判決。
