# 第一幕的受測輸入(shop 這條線)

`orchestrate.py` 會把這個目錄**整包複製**進 run 目錄,不靠人記得放檔案。

```
python3 tools/harness/orchestrate.py <run_dir> examples/shop/harness/act1 [rounds]
```

| 檔 | 誰讀 | 內容 |
|---|---|---|
| `interviewer/prompt.txt` | 訪談者的第一則訊息 | 角色 + 那句原始需求 + 「只能透過我轉述」 |
| `stakeholder/prompt.txt` | 需求方的就位訊息 | 角色 + 只答被問到的 + 不准念文件 |

訪談者的**工作指示**不在這裡 —— 那是 `tools/harness/interview-prompt.md`(harness 擁有,
跨 example 通用),同樣由 orchestrate 複製進去。

⚠️ **這三個檔就是受測品。** 改了任何一個,後續的跑就不能跟先前的比 ——
要改請當成新版本、並在 run 的報告裡標明。理由同
`examples/returns/interview-prompt.md` 為什麼要凍結。
