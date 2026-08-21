# examples/timesheet/harness/act1 —— 第一幕的 template dir

`orchestrate.py` 的第二個引數指這裡。它**自己**把這裡的東西複製進 run 目錄,
run 目錄不要先手動放檔案(手動放就是上次把凍結受測品放進去的原因)。

```
python3 tools/harness/orchestrate.py \
    examples/timesheet/harness/runs/<YYYY-MM-DD-act1> \
    examples/timesheet/harness/act1 \
    6
```

| 檔 | 誰讀得到 |
|---|---|
| `interviewer/prompt.txt` | 只有訪談者 |
| `stakeholder/prompt.txt` | 只有需求方 |
| `stakeholder/spec/SPEC.md` | **只有需求方** —— 他腦中的需求,訪談者看不到 |

⚠️ 跟 `examples/shop/harness/act1` 的**刻意差異**:本案的 `interviewer/prompt.txt`
**不告訴訪談者**「這是中性情境、沒有既有系統、沒有架構模板文件」。shop 那份會送這三樣,
而最後一樣正是「模板既定」造假那一格的答案。這裡沿用 2026-08-19 那跑的判斷:要它自己問出來。
**因此本案的訪談品質不得與 shop 的跑直接比較基線。**
