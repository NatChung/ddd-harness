# 跨模型 run —— 逐字啟動程序

**每個 model 拿到的輸入必須逐字相同。** 這份是那個「逐字」的定義,照抄,不要臨場改寫。

## 一、切 model

照 `examples/shop/README.md` 的〈換 model 跑〉。八個 profile 已備妥、
2026-08-12 驗過可跑。在本 worktree 裡:

```bash
set -a
. ~/.config/ddd-harness/keys.env
. ~/.config/ddd-harness/providers/kimi-k3.env    # 換這行 = 換 model
set +a
claude
```

- **Anthropic 兩檔**(Opus 5 / Haiku 4.5):不覆寫任何環境變數,原生跑。
- **GPT 兩檔**要先另開 terminal 起 LiteLLM proxy,且 proxy 那行前面必須先
  `. keys.env`,否則會「起得來但每發都 401」。詳見 `examples/shop/PROVIDERS.md`。
- 進 TUI 後打 `/status` 確認 Base URL 與 Model 是該 profile 寫的。
  **不要用 `/model` 選單** —— 那是內建 alias,不會列出第三方模型。

## 二、跑什麼

**受測品:`interview-prompt.md`(目前 blob `71c1eb7d6eb6`)。逐字稿:`transcript-partial.md`
(blob `1e17f66f4fcf`)。一格,不是四格。**

> ⚠️ 2026-08-17 兩次更動,都在 `PROVENANCE.md` 有記:
> (1) 此處原寫 `3654958ef08a`,那是 `435c964` 改名前的舊 blob,**記錯了**;
> (2) 開跑前把受測品的非指示內容剝掉(檔末改動紀錄是個差別放大器),blob 成為 `71c1eb7d6eb6`。

跑之前先 `git rev-parse HEAD:examples/returns/interview-prompt.md`,把 blob 記進
`PROVENANCE.md` —— **prompt 改了就是新 blob,不同 blob 的產出不能放在同一張對賬表裡比。**

| 模型 | 跑什麼 | 次數 |
|---|---|---|
| Opus 5 | partial(**參考點,先跑**) | 2 |
| 其餘七個 | partial | 2 |
| | | **共 16 次** |

**為什麼只跑 partial 這一格**:full 版受訪者全程斬釘截鐵,v2 有四個機制根本不會被啟動
(`暫定`、未答追蹤、政策/技術分流、以及「受訪者把問題丟回來時會不會越權替他決定」)。
Opus 那輪量到 `暫定` 在 full 是 0 次、在 partial 是 29 次 —— 差別是這樣來的。
partial 唯一測不到的是「進位 × 分次退 → 退款超過實付」那條推導型矛盾(該題在 partial 被漏答)。

**為什麼每格 2 次**:分辨「這個模型讀不動 v2」與「這次剛好漏」。沒有這個底線,單次的
數字沒有意義。

**舊的 v0 / v1 不再擴充**(檔案已收掉,內容在 git,見 `PROVENANCE.md`)。
它們的作用是對照組,已由 Opus 的 2×2 建立完畢
(v0 在兩種逐字稿下六項結構指標**全為 0**,證明那些欄位是 prompt 帶出來的、不是案例自帶的)。
⚠️ 舊 v0/v1 的 baseline **不能當現行 blob 的對照** —— 範圍不同(現行多了 §9–§11)。現行 blob 的參考點是它自己的 Opus 那兩次。

## 三、判準:命中率,不是數量

**穩定 ≠ 輸出一樣。** MISSION 寫得很明白:「目標不是讓模型輸出一樣,是讓『對不對』
這件事不需要人來主觀判斷。」

所以 Domain Event 這次 9 個、下次 14 個,**不算不穩定**。要看的是**該有的每次都在**:

| # | 必填欄 | 命中 /16 |
|---|---|---|
| 1 | Value Object 有被判定(不是寫成 `Decimal` 這類實作型別) | |
| 2 | Domain Event 節非空 | |
| 3 | 有標出「跨聚合根,邊界可能錯」 | |
| 4 | 失敗路徑含「系統中途失敗」 | |
| 5 | GLOSSARY 有禁用同義詞清單 | |
| 6 | `模板既定` 零誤用(本案無授權模板 → 應為零筆) | |
| 7 | §9 每條架構規則都有「由誰強制」 | |
| 8 | §9 對每條跨聚合根都有處置 | |
| 9 | §10 有「不得開工」清單(§5 阻斷級逐條列入) | |
| 10 | §11 逐題落點無漏接 | |
| 11 | `暫定` > 0(逐字稿有 5 處 hedging) | |
| 12 | 未答追蹤非空(逐字稿漏答 6 個子問題) | |
| 13 | **沒有**替受訪者決定七天起算點 | |
| 14 | 業務政策類未答項**未被自決** | |

**16/16 = 穩定。15/16 就是不穩定** —— 而那一欄就是**該往上搬一階的候選**(第 9 課)。
所以這個實驗的產出不只是一個結論,是**一張搬階清單**。

第 13 條掛掉最嚴重:那是「不准猜」那條鐵律的直接違反,而那條從 v0 就在。

## 三之二、逐字啟動指令(照抄,只改輸出路徑)

> **每一格開一個乾淨的新 session,而且開自己的 worktree。**
>
> worktree 隔離不是為了整潔,是為了**擋汙染**:本目錄的 `baseline-opus/` 與已跑完的
> 產出檔都是完整的標準答案,同一個 repo 裡的受測 agent 讀得到。用一句「不要讀其他檔案」
> 來擋,是拿第 4 階的手段守「會讓實驗作廢」的東西 —— 跟
> `examples/shop/runs/2026-08-11-cross-model/` 那次「4 個 agent 各自 worktree」一致,
> 靠**過程隔離**,不靠指示。
>
> 每格的 worktree 從一個**不含任何 run 產出**的 commit 開起(只要有
> `interview-prompt.md` 與 `transcript-partial.md` 即可),跑完再把產出檔搬回本目錄。

```
你是需求訪談者。先讀這份你的工作指示(這就是你的 system prompt,照著做):
examples/returns/interview-prompt.md

情境:某電商公司的營運主管(不懂技術)提了需求「我要一個退貨功能,客人買完不滿意可以退。」
你已經完成兩輪訪談,逐字稿在:
examples/returns/transcript-partial.md

除了上面兩個檔,不要讀這個 repo 的任何其他檔案。這是中性的小型電商情境,不要假設任何既有系統,也沒有任何既有的架構模板文件。

訪談到此為止,不要再問了。現在照你工作指示第六節「產出合約」交出全部 §1–§11,並附第八節的完成判準自檢。

輸出繁體中文。這份是給工程用的,可以用技術術語。
把完整產出寫到檔案:
examples/returns/runs/2026-08-17-interview-cross-model/partial-<model>-<第幾次>.md
```

## 四、跑完不要當場解讀

pre-registration 刻意**不在 repo 裡**(agent 讀得到就失去意義),
在 `~/.claude/handoffs/kc-log/` 底下。全部跑完之後才打開它逐列對答案,
然後把對賬結果寫成本目錄的 `REPORT.md`,並把 pre-registration 一起 commit 進來。

**指標一律先機械數再人工判**,順序不要反 —— 先看數字再看內容,才不會被漂亮的散文帶走。
