# examples/shop —— 跨模型實驗的 harness 與範例

這個目錄**不是**一般的範例程式,它是 DDD 教學(`lessons/`)第 9 課之後的實驗場:

> 同一份規格餵給不同的 model,兩邊的實作都能被**同一套驗收**明確判定
> ——「對不對」不需要人來主觀判斷。(MISSION.md 的核心成功條件)

## 為什麼這裡有 build 檔

kc-log 本體是文件 repo、明文不加 build tooling。這裡的 Gradle/Spring 檔案是
**教材的一部分**(教學主張「規則要能執行」,範例編不過第 9 課就是空話),
豁免記錄在 `NOTES.md`(原本只存在於 `DDD-學習` branch,2026-08-12 收
worktree 時隨整條線併入 main)。

## 結構

```
examples/shop/
├── spec/        規格包 = 餵給每個 model 的輸入(逐字相同)
│   ├── SPEC.md          功能、GWT 情境、領域規則
│   ├── GLOSSARY.md      詞彙表(Ubiquitous Language)
│   ├── ARCHITECTURE.md  分層與相依規則
│   └── PROMPT.md        固定啟動指令
├── app/         Spring Boot 骨架 = harness 提供的部分
│   └── src/test/…       驗收套件(HTTP 層)+ 機械檢查(ArchUnit)
└── runs/        每次實驗的產出與比對(實驗後才出現)
```

分工的鐵律:**骨架與測試由 harness 提供,實作(`com.shop` 的
`domain/`、`usecase/`、`adapter/`)由被測的 agent 寫。** 驗收只打 HTTP、
不 import 任何實作類別,所以長得完全不同的兩份實作都判得動。

## 跑起來

```bash
cd app
./gradlew test        # 驗收 + 機械檢查
./gradlew bootRun     # 有實作之後,真的起一個 API(H2 in-memory)
```

骨架狀態(沒有任何實作)下,驗收**必須是紅的**、機械檢查是綠的
——紅燈是這個 harness 的功能,不是故障。

## 換 model 跑(跨模型實驗)

八個模型已備妥、全部驗過可跑,涵蓋四家廠商各一強一弱:

| 廠商 | 強 | 弱 | 怎麼指定 |
|---|---|---|---|
| Anthropic | Opus 5 | Haiku 4.5 | **不覆寫任何環境變數**,原生 Claude Code |
| Kimi | `kimi-k3` | `kimi-k2.6` | `providers/kimi-k3.env` / `kimi-k2.6.env` |
| MiniMax | `MiniMax-M3` | `MiniMax-M2.7` | `providers/minimax-m3.env` / `minimax-m2.7.env` |
| OpenAI | `gpt-5.6-sol` | `gpt-5.6-luna` | `providers/gpt-sol.env` / `gpt-luna.env` |

profile 放在 **`~/.config/ddd-harness/providers/`**(**不在 repo 裡** —— 它們指向金鑰,
而本 repo 有其他人的讀取權)。同目錄有 `README.md` 寫了完整用法與已知地雷。

一次 run 的跑法,在該 worktree 裡:

```bash
set -a
. ~/.config/ddd-harness/keys.env                      # 金鑰
. ~/.config/ddd-harness/providers/kimi-k3.env         # 換這行 = 換 model
set +a
claude
```

**GPT 兩欄要先起 proxy**(OpenAI 沒有 Anthropic 相容端點,靠 LiteLLM 轉譯)。
**另開一個 terminal**,proxy 要一直開著:

```bash
set -a; . ~/.config/ddd-harness/keys.env; set +a     # 少這行 → proxy 起得來但每發都 401
litellm --config ~/.config/ddd-harness/litellm.yaml --port 4000
```

第一行不能省:`litellm.yaml` 用 `os.environ/LITELLM_MASTER_KEY` 與
`os.environ/OPENAI_API_KEY` 取值,環境裡沒有就取不到。**失敗長相會騙人**——
proxy 正常啟動、`/health/liveliness` 也回 "I'm alive!",要真的打一發
`/v1/messages` 才看得到 401。

驗證跑對了沒:TUI 裡打 `/status`,看 Base URL 與 Model 是不是該 profile 寫的。
`/model` 選單是 Claude Code 內建的固定 alias,**不會**列出第三方模型,不用去那邊切。

### 三件解讀結果前必須知道的事

1. **GPT 欄多一層轉譯**。Kimi/MiniMax 走各家官方 Anthropic 相容端點,OpenAI 走
   LiteLLM。工具往返已驗過不會壞,但三家**不是完全同構**,報告要寫進限制欄。
2. **弱檔的「弱」不是同一回事**。Kimi/MiniMax 的弱檔連 context 也小
   (262,144 / 204,800),但 `gpt-5.6-luna` 的 context 與強檔 `sol` 相同,
   它只弱在能力與價格。解讀弱檔差異時這兩個變因要分開。
3. **`gpt-5.6-sol` 是通用旗艦,不是 Codex 特化線**(`gpt-5.3-codex`)。刻意選的,
   為了對位「同廠牌能力層級」的框架 —— 是選擇,不是疏漏。

設定本身、五個會咬人的地方(含 `kimi-k2.6` 遇上 `EFFORT_LEVEL=max` 會卡死、
LiteLLM 的兩個版本地雷)、各模型 context window 的查證來源、以及驗證標準,
見 **[PROVIDERS.md](./PROVIDERS.md)**。機器上另有 `~/.config/ddd-harness/providers/README.md`。
