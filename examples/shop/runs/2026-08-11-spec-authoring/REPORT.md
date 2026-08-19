# 三臂比較報告:spec-authoring 實驗(評分依 pre-registration.md,rubric 未改動)

日期:2026-08-11。評審:主 session 逐檔讀原文 + INTERVIEW-LOG 審計,不採信 agent 自報。

## 總評分表

| Rubric | Arm 0(無合約) | Arm A(grill-with-docs) | Arm B(薄 skill) |
|---|---|---|---|
| R1 六決策覆蓋 | ✅ 6/6(餵的,不算本事) | ✅ 6/6(訪談揭露,log 可稽) | ✅ 6/6(訪談揭露,log 可稽) |
| R2 GWT 品質 | 🟡 非 GWT,但 T-01~T-14 字面值斷言**最強**(固定時鐘、seed、精確金額) | 🟡 非 GWT;驗收清單 11 條一行式,可斷言但較粗 | ✅ 唯一真 GWT(S1–S9),具體資料、Then 可斷言;金額單位精度輸 Arm 0 |
| R3 不在範圍槽位 | ✅ 強(「不要預留」+「明確不驗收」雙節) | ✅ 有(SPEC §1 explicit no + ADR no-s)——**來自越出 skill 的自加 SPEC** | ✅✅ 最強:9 項、每項標來源(訪談否決 vs 規格沉默)、收「不要做」+ ASSUMPTIONS 出口 |
| R4 命名紀律 | 🟡 有詞彙表、標準 DDD 詞;**無**「不得另創同義詞」鐵律、無禁用清單 | ✅ CONTEXT.md 每詞 _Avoid_ 欄;無 DDD 型態標注 | ✅✅ 16 詞 + DDD 型態欄 + 鐵律句 + 禁用同義詞/禁用方法名清單 |
| R5 結構落點 | ✅ port 進 usecase、@Entity 只在 adapter 講死;**讀側走 aggregate(無 CQRS 分離)** | 🟡 只引用 starter 四條;介面位置、View Model 位置未寫 | ✅ A1–A5 齊;**Repository 介面放 domain**(參考答案放 usecase——規格沉默處的分歧);讀側可直組 OrderSummary |
| R6 工作契約 | 🟡 有「衝突以驗收檔為準」+完成定義;**無凍結清單、無 ASSUMPTIONS 機制** | ❌ 無(完成定義=測試通過,僅此) | ✅✅ PROMPT.md 全套:凍結清單、範圍、完成定義(全綠+恰兩端點+命名照表+範圍外未實作)、歧義自決規則 |
| R7 訪談品質 | —(對照臂,無訪談) | ✅✅ 13 則、6/6 命中、6 off-script 業務、SPEC 每條 [Qn] 回鏈 log(可稽核性最佳) | ✅✅ 12 則、6/6 命中、唯一觸發「聽不懂講人話」fallback 並改口(Q3b);每題標文件落點 |

## 預測對賬(輸贏照 pre-registration)

| 預測 | 結果 |
|---|---|
| Arm 0 缺 R3 硬結尾 | **預測輸**——它的 out-of-scope 反而最狠(「不要預先建 CANCELLED」) |
| Arm 0 缺 R6 | **預測贏**——無凍結清單、無 ASSUMPTIONS 機制 |
| Arm 0 自行展開範圍 | **預測輸**——刻意收斂(D-14 不預留結構);但代價是 **14 條單方決策**(D-01~D-14)無 stakeholder 驗證機會。nuance:它自標 3 條「建議回頭確認」(改名歷史/時區/幣別清單),有自覺;其餘 11 條連旗標都沒有 |
| Arm A 缺 R2/R3(CONTEXT 不是 spec) | **洞的位置預測贏、agent 行為預測輸**——agent 判斷 skill 產出不足以交付,**越出 skill 自加 SPEC.md** 補洞(附理由)。洞真實存在,但被強模型自我修復;修復物形狀不受控(自創結構,非 GWT) |
| Arm A 缺 R6 | **預測贏** |
| Arm B 形狀齊 | **預測贏**——唯一四檔全齊、唯一真 GWT |
| Arm B GWT 具體度風險 | **部分應驗**——金額單位未定義(unitPrice=1500 是元?分?),Arm 0 的 BigDecimal scale-2 規格反而更嚴 |
| Arm B 訪談較淺 | **預測輸**——12 vs 13 題,深度相當 |

## 汙染檢查

參考答案的特徵 token(`unitPriceCents`、`C-001` 帶連字號、`OrderListItem`、`P-100`)三臂**全數缺席**;三臂自報只讀過自己寫的檔案。無強汙染信號。(Arm 0/A 用了 `statusLabel` 與參考答案同名,屬自然命名,弱信號不採。)

## 結論(對應原始問題:直接用 grill-with-docs 行不行?)

1. **grill-with-docs 的訪談引擎(/grilling)完勝,直接偷**:兩臂訪談皆 6/6 命中、off-script 處置全照 fallback、一次一題附建議答案的品質很高。
2. **但它的產出合約不是 harness 輸入的形狀**:CONTEXT+ADR 明文「不是 spec」。這輪強模型自己越界補了 SPEC——但這是**不受控的自我修復**,換一個模型/換一次運行,補不補、補成什麼形狀,沒有保證(writing-great-skills 的第一美德是 predictability,正是這個)。
3. **薄 skill(約 30 行)買到的是形狀的確定性**:唯一四檔全齊、唯一真 GWT、唯一有凍結清單+ASSUMPTIONS 的工作契約、「不在範圍」還自發標注來源(訪談否決 vs 規格沉默)。
4. **Arm 0 證明合約不是給智力的,是給變異的**:拿到完整逐字稿的強模型,無合約也能寫出斷言最精確的驗收規格——但命名鐵律、凍結契約這些「防下游走樣」的槽位就是不會自己長出來,且 14 條決策全數單方裁定。對照輪 1 教訓:規格沉默處的行為是模型先驗,不是可靠性質。
5. **兩個參考答案沒有、值得回饋給薄 skill 的發明**:(a) Arm B 的「不在範圍」來源標記;(b) Arm A 的 SPEC 條文 [Qn] 回鏈 INTERVIEW-LOG(規格→訪談的 traceability)。(c) 薄 skill 下輪可補:金額單位規則(Money 格式)進產出合約。

## 限制(照 pre-registration)

self-play 洩漏(同 context 持有答案庫,靠榮譽制+log);n=1/臂;三臂同模型(量的是合約形狀差,不是模型差);禁讀 repo 靠指令+自報無硬隔離。
