# 跨模型 harness 的 provider 設定

八個模型、四家廠商各一強一弱,全部驗過可跑(2026-08-12 建置)。
**跑法看 [README.md](./README.md) 的〈換 model 跑〉**;這份記的是設定本身、
查證來源,與會咬人的地方。

金鑰與 profile 都在 **repo 外**:`~/.config/ddd-harness/`
(`keys.env` 為 600、`providers/` 為 700)。原因是本 repo 有其他同事的讀取權。
**這份文件不含任何金鑰材料,也不要加。**

---

## 模型分層

| 廠商 | 強 | 弱 | context(強 / 弱) |
|---|---|---|---|
| Anthropic | Opus 5 | Haiku 4.5 | 原生,不覆寫環境變數 |
| Kimi | `kimi-k3` | `kimi-k2.6` | 1,048,576 / 262,144 |
| MiniMax | `MiniMax-M3` | `MiniMax-M2.7` | 1,000,000 / 204,800 |
| OpenAI | `gpt-5.6-sol` | `gpt-5.6-luna` | 922,000 max input(兩者相同) |

**context window 一律查證、不沿用**:Kimi 兩檔查 `GET api.moonshot.ai/v1/models`;
MiniMax 查官方 API reference 的相容性表(M2.7 的 204,800 是 input+output 合計,
官方 models-intro 頁沒寫,別在那頁找);OpenAI 兩檔查 developers.openai.com 的
model 頁。**弱檔沿用強檔的值會撞 context-length error。**

`*-highspeed` 變體(`kimi-k2.7-code-highspeed`、`MiniMax-M2.7-highspeed`)
官方寫明「同能力、更快」,**不是弱檔**,不要拿來當弱端。

## 接法

Kimi 與 MiniMax 都有**官方 Anthropic 相容端點**,直接靠 `ANTHROPIC_BASE_URL`
覆寫,規格包與骨架一字不改:

- Kimi:`https://api.moonshot.ai/anthropic`(`platform.moonshot.ai` 已導向 `platform.kimi.ai`)
- MiniMax:`https://api.minimax.io/anthropic`(國際站;中國站是 `api.minimaxi.com`)

OpenAI **沒有**相容端點,墊一層 LiteLLM 轉譯,設定在 `~/.config/ddd-harness/litellm.yaml`。

### 為什麼不寫進 `~/.claude/settings.json`

兩家官方文件都叫人寫那裡,**本專案刻意不照做**:那會綁架整台機器平常在用的
Claude Code。而且 `settings.json` 的 `env` 值**優先於** shell export,寫了反而
蓋掉 per-run profile。harness 要的是「一次 run 一組環境」,不是全域切換。

---

## 五個會咬人的地方

1. **只設一部分模型階變數會靜默失效。** Kimi 官方列了對照表:haiku 階沒設 →
   背景標題/摘要任務掛;`CLAUDE_CODE_SUBAGENT_MODEL` 沒設 → subagent 降級。
   **對分層 subagent 實驗尤其致命。** 六個 profile 因此都把
   opus/sonnet/haiku/fable/subagent 五階全指到同一個模型。

2. **`CLAUDE_CODE_EFFORT_LEVEL=max` 會讓 `kimi-k2.6` 無限卡住。** 實測:設了之後
   連 `claude -p "say pong"` 都不回應;未設則幾秒回,對照實驗只差這一個變數。
   Kimi 官方 Claude Code 頁把 max 當通用建議,但**那頁是以 k3 為主寫的**。
   **六個 profile 現在一律不設**,除了避開這個 bug,也讓強弱對照少一個變數。

3. **LiteLLM 有版本地雷兩個**:
   - **供應鏈**:PyPI `1.82.7` / `1.82.8`(2026-03-24)遭投毒,含憑證竊取與常駐
     後門(TeamPCP 經 Trivy CI/CD 入侵)。兩版已下架,目前裝 **1.96.2**。
     **這台機器上有三家 API key,升級前先確認版本不是那兩個。**
   - **相依**:litellm 需要 `fastapi.dependencies.utils.get_flat_dependant`,
     該函式在 **fastapi 0.141+ 已移除**(0.140.0 還有)。pipx 預設會裝到 0.141.x
     → proxy 起不來,而且錯誤訊息會誤導(`ImportError` 之後接
     `ModuleNotFoundError: No module named 'proxy_server'`)。
     修法:`pipx inject litellm 'fastapi==0.140.0' --force`。**重建環境要一起做。**

4. **`--port` CLI 參數會被 `litellm.yaml` 靜默蓋掉。** 2026-08-12 實測:下
   `litellm --config ... --port 4000`,實際 bind 在 **1452**(yaml 裡的值贏),
   而且**沒有任何警告**。後果是 `ANTHROPIC_BASE_URL` 指向 4000 的 GPT 欄整欄打不通,
   但 proxy 看起來是活的。
   **啟動後必驗實際 port**(`lsof -nP -iTCP -sTCP:LISTEN | grep -i litellm`),
   不要相信自己下的參數。要換 port 就改 yaml。

4. **`/model` 選單不會列出第三方模型。** 那是 Claude Code 內建的固定 alias 清單,
   不用去那邊切。**驗證落點一律看 `/status`** 的 Base URL 與 Model。

5. **OpenAI 額度 2026-10-01 到期。** 十月前沒用完就作廢。以實測推算,GPT 兩欄跑完
   一輪完整實驗(照輪 1 的 ~100k tokens/run 規模)約 $2–5,額度充裕。
   該額度的來源**查不出來**:後台沒有任何一頁標示,帳單歷史對不上,促銷頁為空;
   唯一線索是「它會過期」(自購 credits 不過期)→ **傾向非自購,但這是推論,
   不是查到的事實**,不得當定論引用。

---

## 驗證標準(下次改動後要重跑的那一套)

**認證層過了不算通。** harness 的 run 全是 agentic 流量(tool_use / tool_result /
thinking 區塊),純文字 ping 過了不代表工具往返在轉譯中不會壞 —— 尤其 GPT 那條
多墊一層。所以關卡是:

> **source 該 profile 檔** → `claude -p "用 Bash 工具跑 ls 並逐字回報檔名"`
> → 三個 marker 檔名逐字正確。

**必須 source 檔案,不能手打 export** —— 驗的是 profile 檔本身,不只是模型。

### 這條標準第一次寫下時是假的,而它自己抓到一個 bug

最初只有三個 profile 是 source 檔案跑的,另外三個是在 profile 檔還不存在時用
手打 export 驗的(其中一個還在驗完後被改過),筆記卻寫成六個都驗過。補跑之後:
兩個通過,**`kimi-k2.6` 掛掉** —— 就是上面第 2 點那個 bug。

照第 9 課的階梯讀:「六個都驗過」當時只住**第 5 階**(筆記裡一句話),沒有任何
東西擋著它變成假的。搬到**第 2 階**(真的逐一 source 檔案實跑)**一搬就抓到 bug**。
**收件驗證的標準自己也需要被驗證** —— 與輪 1「收件驗 commit parent」同源。

---

## 解讀結果前必須知道的三個不對稱

1. **GPT 欄多一層轉譯。** Kimi/MiniMax 走官方相容端點,OpenAI 走 LiteLLM。
   工具往返驗過不會壞,但三家**不是完全同構**,報告要寫進限制欄。
2. **弱檔的「弱」不同質。** Kimi/MiniMax 的弱檔連 context 也小,但 `gpt-5.6-luna`
   的 context 與強檔 `sol` 相同,它只弱在能力與價格。這兩個變因要分開解讀。
3. **`gpt-5.6-sol` 是通用旗艦,不是 Codex 特化線**(`gpt-5.3-codex`)。刻意選的,
   為了對位輪 1 的「同廠牌能力層級」框架 —— 是選擇,不是疏漏。

---

## 還沒做的:把換 model 這件事搬上第 2 階

目前「哪個 profile 對應哪個 model、要先起 proxy」住在 **第 4 階**(README 的散文)。
**沒有任何機制擋著 agent 不讀 README 就開跑** —— 真發生的話它會拿原生 Claude Code
跑完、產出一份錯標籤的樣本,而且**不會報錯**。

搬上第 2 階的做法(屬輪 2 的 launcher 工作,尚未動工):

- **launch 前**:驗 `ANTHROPIC_MODEL` 確實等於這次 run 預期的值(GPT 欄另驗 proxy 活著)
- **收件時**:把實際生效的 model 與 base URL 記進該 run 的 metadata,
  與輪 1 已在做的「驗 commit parent == 骨架 commit」並列
