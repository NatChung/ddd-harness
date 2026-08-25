# 23 — 對答案(2026-08-25)

預測檔:`23-PREDICTION.md`(commit `f6ab595`,寫在守衛之前)。
守衛:`tools/harness/spec_store.py` 的 `check_placeholders`,接在 `build_store` 開頭、
`_check_shape` 之前。測試:`tools/harness/test_prefill.py`。

## 預測之後、對真實 yaml 跑之前,設計動過兩處(先講,不藏)

預測寫完、守衛第一版接上去跑全套 pytest:**42 紅**(236 → 194 綠)。
沒有一條是真實 yaml,全是儀器自己的測試語料抓到的。兩處都改守衛,**一個測試檔都沒動**:

| # | 抓到什麼 | 證據 | 改成 |
|---|---|---|---|
| (a) | `provenance_ref: "[Q1]"` 整格被判成方括號佔位符 | `test_glossary.py` / `test_domain_contract.py` 有 **40 格**拿 `[Qn]` 當合法值 —— 那是這個 repo 的來源標記寫法(provenance `Qn` 配 `[Qn] …`),是引用不是便條 | 方括號 regex 加負向前瞻 `^\s*\[(?!Q\d+\])[^\]]*\]\s*$`;`[待補]` / `[role]` / `[]` 照擋。**票裡釘的原 regex 對儀器語料是假陽性**,對三份真實 yaml 不是(見下),因為真實 yaml 的 `[Q12]` 後面都接了本文 |
| (b) | `provenance_ref: "   "` 被第 0 階先擋 | `test_harness.py::test_來源為空寫不進去`(本票不准動)斷言空白格的訊息是 **「schema 擋下來了」** —— 它把「空白格 = 第 1 階」釘死了 | 第 0 階的「空字串」收**恰好 `""`**,「只有空白」不收,留給 schema 的 `length(trim(x)) > 0`。同一條規則兩份載體會漂(`_check_glossary` docstring 自己講的原則) |

這兩條是儀器語料抓到 pre-scan 沒抓到的東西。PREDICTION **不回改**(回改就毀掉這個 repo 唯一的量法),
P1–P5 照原文對答案。

## 對答案

| # | 預測 | 實際 | 判定 |
|---|---|---|---|
| P1 | 語料 A:第 0 階 0 格;`import` 仍 exit 1,錯誤清單與改前逐字相同,無「第 0 階」 | 掃 111 個字串格,**命中 0**;exit 1;五條訊息與改前逐字相同(缺 `wire_contract` + 4 條 `list_row_exists`),沒有「第 0 階」 | **命中** |
| P2 | 語料 B:第 0 階 0 格;exit 0 | 掃 293 格,**命中 0**;exit 0 | **命中** |
| P3 | 語料 C:第 0 階 0 格;exit 0 | 掃 555 格(三檔合併),**命中 0**;exit 0 | **命中** |
| P4 | 拿掉豁免,語料 B 恰好 1 格 `…rejected_requests[0].customer_id`(S7);A、C 仍 0 | 探針(scratch script,不進正式碼):B **恰好 1 格** `acceptance_scenarios[6].rejected_requests[0].customer_id = ''`;A 0、C 0。另跑「連只有空白也算」:仍 1 / 0 / 0 | **命中** |
| P5 | pytest 236 → 236 + 新檔,既有一條都不變紅 | **268 passed**(236 + 32);`test_negative_scenarios.py` 那條 S7 `customer_id == ""` 綠 | **命中**(但中間經過上面那 42 紅,是改守衛不是改測試才回綠) |

**三份真實 yaml 各命中幾格:A 0、B 0、C 0。** 沒有假陽性、也沒有真漏 —— 但要老實說:
「零命中」在這三份上**證明的是守衛不誤傷**,不證明它抓得到東西(這三份本來就沒有人寫佔位符)。
抓得到東西的證據在 `test_prefill.py`:14 種佔位符寫法各一例被拒(parametrize),
路徑印到 `acceptance_scenarios[i].steps[0].items[0].product_id` 這種深度。

另驗:票裡釘的**原**方括號 regex(沒有 `[Qn]` 前瞻)對三份真實 yaml 也是 0 命中 ——
所以 (a) 那條收窄在真實語料上沒有差別,差別只在儀器語料。

## 順手驗到的:第 1 階空白 CHECK 的覆蓋缺口(不在本票修)

票說「`CHECK (length(x) > 0)` 涵蓋哪些欄,沒驗過」。(b) 之後第 0 階不收 `"   "`,
那些格就全靠第 1 階,所以用 `fixtures/negative-scenarios.yaml` 探了幾欄(scratch script):

| 欄 | `"   "` 填進去 | 狀態 |
|---|---|---|
| `acceptance_scenario.given_when` | 擋下(schema) | 驗過,對照組 |
| `architecture_rule.provenance_ref` | 擋下(schema) | 驗過(`test_來源為空寫不進去`) |
| **`acceptance_scenario.id`** | **靜默通過,exit 0** | **驗過,缺口** |
| **`acceptance_scenario.proxy_for`** | **靜默通過,exit 0** | **驗過,缺口** |
| `assertion.expected_text` / `assertion.field` | 沒探到(fixture 的 S1 只有 `status_is`) | **推斷**是缺口(schema 那兩欄沒有 `length(trim)` CHECK),未驗 |

`id` 是 PRIMARY KEY TEXT,空白也是合法主鍵;`proxy_for` 是選填散文欄。這兩格寫 `"   "`
今天會進庫。**建議開一張票補 schema**(第 1 階的事,不是第 0 階;本票不動 `schema.sql`)。

## 沒做到 / 偏離票文的

1. 「空字串」只收 `""`,不收 `"   "` —— 被 `test_harness.py::test_來源為空寫不進去` 逼的,見 (b)。
2. `[Qn]` 整格放行 —— 見 (a)。票的原 regex 會把儀器語料 40 格判成佔位符。
3. `None`(`wire_field:` 整個留空)不算佔位符 —— 票的清單沒有它,現有選填語意也靠它。
4. 離開碼維持 1,沒有為第 0 階另開一個碼 —— 票沒要求;訊息行首「第 0 階 佔位符:」已足以跟
   「schema 擋下來了:」分開。要不要獨立離開碼,留給 `PIPELINE.md` 離開碼表那組的下一次對齊。
