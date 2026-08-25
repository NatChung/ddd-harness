# 31 — spec yaml 沒有 canonical-format 檢查:同一份規格兩種寫法,diff 看不出是內容變了還是格式變了

**What to build:** `spec_store.py canon <yaml>`:parse → 用固定序列化重寫 → 逐位元組比,不同就印 diff、exit 1;
`verify_generated.py` 那招對 spec 自己再做一次。

**Blocked by:** None

**Status:** needs-triage —— 2026-08-25 survey §3 第 8 條(fspec `check` 的 Gherkin byte-parity),低優先;尚未開工。

## 哪裡壞了

生成物有 `verify_generated.py` 逐位元組比;spec yaml 本身沒有。幕二 agent 換個 key 順序、換個引號,
`git diff` 就一片紅,看不出語意有沒有變。票 15 那個「誠實寫在註解裡」的問題也跟這有關:canonical 序列化
會把註解丟掉,**所以這支要在報表印「本檔有 N 行註解,canonical 版不含」**,不然它會靜靜地把票 15 的證據洗掉。

## 慣例(ADR 0007)

「spec yaml 用 canonical 格式 commit」—— 先 prose-only, unenforced;等量過三份真實 yaml 有多少差再決定要不要進閘門。

## 完成的定義

- `31-PREDICTION.md`:三份真實 yaml 各差幾行(預期 `2026-08-19-act2` 最多,因為它三檔手寫註解最多)。
- `test_spec_canon.py`(新檔)。
