# 23 — 預測(寫在跑之前,2026-08-25)

對象:`spec_store.py import` 的第 0 階「佔位符守衛」,對三份真實 yaml 跑。
本檔在守衛**寫出來之前、跑之前**落地,單獨 commit,跑完寫 `23-RESULT.md` 對答案。

## 受測語料(只讀,不動)

| 語料 | 檔 | 今天(改之前)`import` 的結果 |
|---|---|---|
| A | `examples/shop/harness/runs/2026-08-18-act2-opus/agent-acceptance.yaml` | **exit 1**(驗過):缺 `wire_contract`、4 個 `list_row_exists` 未先斷言 —— 都是第 2 階,是 8/18 之後 `spec_store.py` 收緊造成的既有狀態,**與本票無關** |
| B | `examples/shop/harness/runs/2026-08-18-act2-rerun/agent-acceptance.yaml` | **exit 0**(驗過) |
| C | `examples/shop/harness/runs/2026-08-19-act2/{acceptance,contracts,glossary}.yaml`(三檔一起匯) | **exit 0**(驗過) |

## 守衛的設計(預測所依據的形狀)

- 走 parse 後的整棵樹,**只看 `str` 值**;key 不看、`None` 不算(`wire_field:` 留空、
  `use_instead:` 留空是既有的選填語意,不在票的清單裡)、數字 / bool / list 不算。
- 判準是「整格只有佔位符」,每條 regex 頭尾都錨:
  - 空字串 / 只有空白
  - `^\s*\[[^\]]*\]\s*$`(整格一個方括號)
  - `^\s*<[^>]*>\s*$`(整格一個尖括號)
  - `^\s*\?+\s*$`(整格只有問號)
  - `^\s*(TODO|FIXME)\b`(**起頭**錨定:`TODO: 待補` 整格就是一張便條,句中出現
    `TODO` 的本文不算)
- **一條豁免**:`acceptance_scenarios[*].rejected_requests[*].customer_id` 可以是空字串。
  這不是設計取捨而是儀器自洽的必然:`schema.sql` L282 刻意拿掉那格的
  `length(trim(...)) > 0`(S7 未登入)、`_check_rejection_scenario` 明寫「要送空的請寫 `""`」、
  `fixtures/negative-scenarios.yaml:111` 就是 `customer_id: ''`,而
  `test_negative_scenarios.py:61` 直接斷言它等於 `""`(那個檔本票不能動)。

## 動手前的 pre-scan(誠實揭露:預測不是盲的)

寫預測前對五個檔 grep 過三種形狀,結果如下(驗過):

- `TODO` / `FIXME` / `???`:**0 命中**。
- 整格只有 `[...]` 或 `<...>`(含引號包住、含 block scalar 內獨立一行):**0 命中**。
  五個檔裡的方括號都是 `[Q12] — SPEC.md L83…` 這種「後面有本文」的引用,不是整格。
- 空字串:**1 處** —— 語料 B 第 276 行 `customer_id: ""`(S7 未登入,YAML 註解明寫
  「刻意送空字串」)。語料 C 的 `wire_field:` / `use_instead:` / `no_named_test_reason:`
  留空共 20 多處,但 YAML 解析後是 `None` 不是 `""`,不在守衛的視野裡。

## 預測

| # | 預測 | 若落空代表什麼 |
|---|---|---|
| P1 | 語料 A:第 0 階 **0 格**命中;`import` 仍 exit 1,而且錯誤清單**與改之前逐字相同**(第 2 階的那 5 條),訊息裡**沒有**「第 0 階」字樣 | 有命中 = 假陽性(A 是 8/18 的產物,沒人寫過佔位符);訊息變了 = 守衛污染了既有階層 |
| P2 | 語料 B:第 0 階 **0 格**命中;`import` 仍 exit 0 | 命中 1 格且是 `S7.customer_id` = 豁免沒接上(bug);命中別處 = 假陽性或真漏,逐格記 |
| P3 | 語料 C:第 0 階 **0 格**命中;`import` 仍 exit 0 | 同上;C 是三檔合併匯入,若命中在 `glossary_terms` / `domain_contracts` 要特別看是不是 `None` 被誤判成空字串 |
| P4 | 若把豁免拿掉(naive 版),語料 B 會命中**恰好 1 格**:`acceptance_scenarios[?].rejected_requests[0].customer_id`(S7);A、C 仍 0 | 多於 1 格 = pre-scan 漏看了;0 格 = 守衛連空字串都沒在看 |
| P5 | `cd tools/harness && python3 -m pytest`:236 → 236 + 新檔的測試數,**既有 236 一條都不變紅**(尤其 `test_negative_scenarios.py` 那條斷言 S7 `customer_id == ""` 的) | 紅 = 豁免路徑寫錯 |

## 不預測的(本票不碰)

- YAML 註解裡的東西(票 15)。守衛看的是 parse 後的值,註解已經不在了。
- `None`(整個 key 留空)算不算「沒填」—— 票的清單沒有它,現有選填語意也靠它,本票不動。
