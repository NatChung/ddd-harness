# 分層 subagent 管線實驗報告(對賬依 pre-registration.md,預測表未改動)

日期:2026-08-12。3 樣本(OL1=Opus、HL1/HL2=Haiku 4.5)× 3 層串行,
樣本間並行。對照組 = 輪 1 單 agent 四樣本(O1/O2/H1b/H2b)。
兩軸 review 照輪 1 規格(6 個 Opus reviewer,互不見彼此)。

## 結論一句

**分層消掉的是「跨層便利性妥協」的*機制*,消不掉洞的*形狀***:
INTERFACE-REQUESTS 三樣本九層**零請求**、越界退件零、修復輪零——adapter
從來不需要向內層要後門,H2b 那種「為了持久化在 domain 開洞」的壓力鏈
被物理拆掉了;但 H2b 後門的**同型物照樣在 HL2 出現**(`Order.reconstruct`
公開 factory 收任意 total/status 不驗一致性)——這次的成因是 domain agent
**自己的投機通用性**(替不存在的讀回需求預留路徑),不是跨層壓力。
規格沉默類的洞(INNER JOIN 掉單、addItem 不原子)照預測再現。
**「分層管過程、規格管沉默,互不替代」的正交結論成立,且多了一條:
過程隔離拆得掉誘因,拆不掉模型自己的先驗。**

## 通過率(非指標,照預測無差異)

| 樣本 | 整合測試 | 驗收 | 退件 | 修復輪 | IR 請求 |
|---|---|---|---|---|---|
| OL1 | 58 全綠 | 5/5 | 0 | 0 | 0 |
| HL1 | 74 全綠 | 5/5 | 0 | 0 | 0 |
| HL2 | 70 全綠 | 5/5 | 0 | 0 | 0 |

## 逐洞對賬(凍結預測 → 實際)

| 洞(輪 1) | 預測 | 實際 | 判 |
|---|---|---|---|
| 🔴 H2b public 建構子後門 | 消失(寫隔離拆誘因) | **半再現**:HL2 `Order.reconstruct` 公開收任意 items/total/status、零驗證——同型後門,但係死碼(production 零呼叫者,且 `OrderItem` package-private 令 adapter 根本無法使用它);OL1 的 `reconstitute` 會重算總額驗前置,reviewer 判非破口;HL1 無此路徑 | **半輸**——機制(跨層壓力)如預測被拆,形狀(任意 total 後門)仍由投機通用性長出 |
| 🔴 H2b 幣別檢查可跳過 | 再現(不解) | 未再現:三樣本幣別檢查皆不可跳過(HL1 甚至雙重檢查) | 輸(輸得好) |
| 🟠 addItem 失敗不原子 | 再現(不解) | **HL2 再現**(先 `items.add` 後重算,跨幣別例外留髒 Aggregate——兩軸 reviewer 皆列最嚴重);OL1/HL1 原子(OL1 先算後改,HL1 全驗證後變動) | 中 |
| 🟠 INNER JOIN 掉單 | 再現(不解) | **HL1、HL2 皆再現**(INNER JOIN customers + 下單不驗顧客 → 201 但列表永不出現);OL1 雙 LEFT JOIN 乾淨 | 中 |
| 🟡 壞死碼毀 placedAt | 不押注,列觀察 | 弱形態:HL2 的 re-save 會重寫 placed_at + 重建明細(目前不可達);OL1/HL1 讀取路徑乾淨 | 觀察:注意力假說無強證據 |
| 🟡 捏造 ASSUMPTIONS | 再現(不解) | 輕度抽查未見 H1b 型捏造;反向信號:六個 agent **自首**白名單外 git 指令(見執行偏離)。完整逐條真偽審計未做,列後續 | 未定(淺查) |
| 零自發測試(Haiku) | 部分改善(prompt 效果) | 大幅改善:Haiku 各層 30–54 條單元測試;**但品質洞轉移到測試層**——HL1/HL2 的 no-setter 反射測試皆恆真(掃不到任何真 setter),HL2 的 reconstruct 正好從 `set*` 字面檢查旁邊走過 | 中(綁定標註:prompt 要求自驗,非隔離效果) |

## 分層才看得見的新量測物

1. **INTERFACE-REQUESTS = 0(9 層全部)**:內層先行、外層適配的串行順序下,
   domain 在不知 JPA 的情況下設計的 API 對 usecase/adapter 全部夠用——
   跨層妥協的誘因鏈沒有形成過。這是單 agent 模式下不可見的負結果,
   價值在於:H2b 型後門若再出現,可排除「外層要求」這條成因。
2. **品質梯度再現且看得見**:OL1(零硬違規,findings 集中在投機通用性)
   > HL1(無硬違規;恆真測試、INNER JOIN、409 語義誤映)> HL2(兩條 🔴:
   不原子 + reconstruct 後門;INNER JOIN;ORDER BY 越界)。與輪 1 的
   O > H 梯度一致——分層沒有抹平模型能力差。
3. **新洞型:規格明列「不要做」仍越界**——HL2 `ORDER BY o.order_id`
   (SPEC 不在範圍明列排序;且按隨機 UUID 排序,承諾了無意義的順序)。
   輪 1 O2 也有 ORDER BY 越界:此洞與分層/單 agent 正交,住在「明確不在
   範圍」的執行力,輪 2 候選。
4. **三樣本共同張力(架構規則的系統成本,非個別失誤)**:總額規則
   Java/SQL 雙實作、無測試綁定兩者——是「Query 側不經 Aggregate」規則
   逼出來的;三份 review 各自獨立指出。教材素材。

## 執行記錄

| 樣本-層 | model | agentId | tokens | 耗時 |
|---|---|---|---|---|
| OL1-domain | opus | a28ea771d9e8011b2 | 138,324 | 316s |
| OL1-usecase | opus | a4f04724f17bf6f1d | 155,444 | 462s |
| OL1-adapter | opus | a5cb6848dcd8ad2b9 | 166,699 | 420s |
| HL1-domain | haiku | a2d3a1433b738586d | 64,820 | 210s |
| HL1-usecase | haiku | a80671b5c4bbf579d | 63,926 | 359s |
| HL1-adapter | haiku | a40d7574d84a85d17 | 77,812 | 308s |
| HL2-domain | haiku | a145cb3658bfed112 | 62,408 | 260s |
| HL2-usecase | haiku | a88dc026116591015 | 67,096 | 287s |
| HL2-adapter | haiku | aabc4b0ddca62a94c | 84,463 | 285s |

樣本合計:OL1 ≈ 460k、HL1 ≈ 207k、HL2 ≈ 214k tokens(實作端,不含
review 6 agent ≈ 1,026k)。產物在本 repo 分支:`layered/<樣本>-<層>` 與
`layered/<樣本>-integration`(worktree 在 scratchpad,重開機即失;
branch 是持久紀錄)。收件記錄檔在 `records/`。

### 執行偏離(照實列)

1. **OL1/HL1 的 domain 層是「中斷+續作」**:第一次 batch 被 Nat 中斷,
   兩個 worktree 留下同模型 agent 的未 tracked 半成品;續作 agent(同模型)
   驗證並補完。模型歸屬未混,但這兩個樣本的 domain 層非單次完成
   (HL2 為乾淨單次)。
2. **白名單外 git 指令(全部自首、範圍皆僅自身 HEAD)**:OL1-domain、
   HL1-domain、HL2-usecase、OL1-adapter、HL1-adapter、HL2-adapter 各跑了
   `git log`(±`git diff HEAD~1`)確認自己 commit 落地。誠實性正信號,
   合規性負信號:「只准 status/diff/add/commit」的條款擋不住這個慣性。
3. OL1-usecase/adapter 讀了 harness 背景任務的 stdout 檔(執行環境管線,
   非任務輸入,已自首)。
4. 收件驗證(白名單 diff、親跑測試、鐵律檢查)全程由 parent 機械執行,
   9 包全 CLEAN、0 退件——執行偏離不含任何越界寫入。

## 限制

- Treatment = 隔離 + per-layer prompt **綁在一起**(pre-registration 先認),
  「自發測試改善」「domain API 先行設計」都無法單獨歸因給隔離。
- n=1/樣本組合;Haiku 兩樣本間差異大(HL1 無硬違規、HL2 兩條 🔴)——
  同型雙樣本的雜訊底線正好派上用場:「分層修不掉 Haiku 的洞」的證據
  以 HL2 為準,「分層下 Haiku 也可能乾淨」以 HL1 為準,兩者都只有 n=1。
- Reviewer 全 Opus 且與 OL1 實作同模型(輪 1 同款限制)。
- 讀隔離靠物理缺席(強),但 agent 有 .git 可達性;禁讀其他 ref 靠條款
  +自首(弱)——偏離 2 顯示條款確實會被小幅超越。
- spec/ 與骨架逐位元組停在 `4567d31`(收件後與 review 後各驗一次,皆過)。
