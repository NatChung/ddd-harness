# DDD × Agent Harness

一套讓 AI agent 的產出**不隨著換模型而漂移**的開發 workflow,加上把它教出去的十一課教材。

核心主張很短:DDD 處理的問題是「人跟人之間語言含糊,做出來的軟體就跟著含糊」——
LLM agent 有一模一樣的失效模式,只是它填補含糊的方式是**照訓練分佈猜一個看起來合理的**。
所以 DDD 的語言與邊界,加上 BDD 的可執行驗收,就是這個 harness 的骨架。

完整立論見 [MISSION.md](./MISSION.md)。

> **語言**:教材與筆記是繁體中文,DDD / BDD 術語保留英文原文
> (Bounded Context、Ubiquitous Language、Aggregate、Given/When/Then)。

---

## 一、教材(十一課)

`lessons/` 底下是獨立的 HTML,不需要 build,瀏覽器直接開。
目錄頁是 [`index.html`](./index.html)(GitHub 上不會 render,要 clone 下來開)。

| 課 | 主題 |
|---|---|
| 0000 | 五級演化 —— 從照抄流程到機械驗收(開場課) |
| 0001 | Ubiquitous Language —— 第一道閘門 |
| 0002 | Bounded Context —— 邊界 |
| 0003 | Given/When/Then —— 機械判定 |
| 0004 | Aggregate —— 一次任務的大小 |
| 0005 | 簡潔架構 —— 三原則與爆炸半徑 |
| 0006 | CQRS —— 讀與寫的不對稱 |
| 0007 | Event Storming —— 產物從哪來 |
| 0008 | Design by Contract —— 這是誰的錯 |
| 0009 | Pattern Language —— 讓它會長大 |
| 0010 | 訪談 —— 一句話到驗收(1346 行,拿前九課走完一次真的訪談) |

配套:`practice/`(交錯練習)、`reference/`(參考卡)、
`learning-records/`(這套教法在一個真人身上跑過的紀錄,含答錯的題)。

## 二、harness(五幕管線)

```
「我要一個系統,客人能下單,我能看到所有訂單。」
        │
   幕一 訪談    orchestrate.py         兩個 agent 互相訪談 N 輪 → 散文規格
        │ SPEC-draft.md
   幕二 落檔    run_act2.sh → agent    散文 → yaml → spec.db  ⚠️見下
        │ spec.db(結構化,唯一真相)
   幕三 生成    gen_acceptance.py      零模型、決定性 → 可執行的 Java 驗收
        │        gen_archunit.py
   幕四 實作    agent 照 PROMPT 填骨架 → 驗收全綠
        │ 洞
   幕五 review  洞 → 搬階 → 改 harness → 重跑證明它掉不了
```

**幕三沒有模型。** 從 yaml 到可執行的 Java 驗收之間一次模型都沒有,所以那段可重跑、
逐字相同——`verify_generated.py` 重新生成一次跟 commit 的比,不一樣就紅。
「生成物被手改」因此變成量得到的事件。

自己跑一次(~0.1 秒,離線,只寫暫存目錄):

```bash
python3 tools/harness/verify_generated.py \
  examples/shop/harness/runs/2026-08-19-act3 \
  examples/shop/harness/runs/2026-08-19-act2/{acceptance,contracts,glossary}.yaml
```

它從 2026-08-19 那三個 yaml 重建 `spec.db`、重新生成 Java,跟 `act3/` 已 commit 的產出
**逐位元組**比。順帶注意輸出裡的「【不適用】—— 不是通過」那一行:一條檢查沒東西可查時
自成一類,不折進通過的計數裡(見 `CONTEXT.md` 的**不適用**詞條)。

⚠️ **幕二的受測品已經跟素材漂了**:`examples/` 裡 2026-08-19 那一跑產出**三個** yaml
(`acceptance` / `contracts` / `glossary`),但現在的 `run_act2.sh` 要求**四個**——票 16 補了
`architecture.yaml`。所以 `act2/` 沒有 `architecture.yaml` 是對的、不是漏掉,但**現在重跑
第二幕會拿到跟素材對不起來的形狀**。

⚠️ **幕五的兩個詞**:「洞」= 這一跑暴露出來、harness 擋不住的缺陷;
「搬階」= 把一條原本靠自覺守的規則,往上搬成機械擋得住的(五級階梯見 `MISSION.md`)。

逐段的輸入 / 工具 / 產出 / **驗過沒有**,見 [`tools/harness/PIPELINE.md`](./tools/harness/PIPELINE.md)。

### 跑起來

```bash
pip install pytest pyyaml
cd tools/harness && python3 -m pytest      # 229 passed
```

**相依講精確一點**:各支檢查器本身只用 stdlib,單獨跑不需要裝東西;
但**跑測試需要 `pytest`**,而**匯入 spec yaml 需要 `PyYAML`**
(`spec_store.py` 的 yaml 路徑、`test_negative_scenarios.py`)。JSON 路徑不需要。

各支檢查器獨立可跑:`landing_check.py`(答案有沒有落點)、`provenance_check.py`(來源標記分診)、
`glossary_check.py`(對譯檢查)、
`contract_triage.py`(契約分診)、`vacuous_tests.py`(假驗收分診)、
`package_landing_check.py`(宣告的 package 有沒有 class)、`verify_generated.py`(生成物有沒有被手改)。

## 三、實跑紀錄

`examples/shop/harness/runs/` 有 11 跑的完整素材。最完整的一條是 **2026-08-19**,
五幕第一次全部跑通:

| 幕 | 目錄 | 產出 |
|---|---|---|
| 一 | `2026-08-19-act1-human-stakeholder/` | 六輪 30 題(**需求方是真人**,不是 agent)→ 550 行規格 |
| 二 | `2026-08-19-act2/` | 三個 yaml,opus-5、21 turns |
| 三 | `2026-08-19-act3/` | 兩個 Java 測試檔,零模型生成 |
| 四 | `2026-08-19-act4/` | 9/9 全綠 + 23 個實作 class |

⚠️ **「全綠」的真實含意**:9 條裡只有 1 條是真情境,17 條 GWT 只有 1 條、17 條契約只有
8 條走到實作面前。這條線最有價值的產出是**它自己的缺陷清單**,不是那個綠燈。
未結的洞在 `.scratch/ddd-harness/issues/`(18 張票,9 張還活著)。

`examples/specimens/` 收標本——目前一個:一條**恆真**的 no-setter 反射測試,
不管實作怎麼寫都會綠,而且看起來很像在守一條真的領域規則。

## 四、怎麼讀這個 repo

| 想知道 | 讀 |
|---|---|
| 為什麼做這個 | [MISSION.md](./MISSION.md) |
| 這些詞是什麼意思 | [CONTEXT.md](./CONTEXT.md) —— 10 個詞,每個都附「別跟誰搞混」 |
| 管線每一段的證據 | [tools/harness/PIPELINE.md](./tools/harness/PIPELINE.md) |
| 為什麼設計成這樣 | [docs/adr/](./docs/adr/) |
| 逐日的決定與教訓 | [NOTES.md](./NOTES.md)(1208 行) |
| 來源出處 | [RESOURCES.md](./RESOURCES.md) |
| 還沒解決的 | [.scratch/ddd-harness/issues/](./.scratch/ddd-harness/issues/) |

---

## License

[MIT](./LICENSE) —— code 與教材都是。拿去用、改、教都可以,保留版權聲明就好。

---

*匯出自 `kc-log` repo 的 `DDD-2` 分支 @ `8aecc08`(2026-08-19)。原 repo 是私人工作筆記,
DDD 的部分拆出來獨立成本 repo;完整的逐 commit 歷史留在原處。*

*⚠️ 因此 `CONTEXT.md`、`NOTES.md` 與各張票裡引用的 commit hash(`4567d31`、`215ae8c`、
`18bf044` 等)**在這個 repo 解不開** —— 本 repo 只有一個 commit。那些 hash 指向的是原
repo,而原 repo 是私有的。引用它們的地方講的事實本身在檔案裡都看得到,hash 只是出處註記。*
