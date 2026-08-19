# usecase agent prompt(佔位符 `{{WORKTREE}}` 由 parent 於 launch 時代入)

你是 usecase 層的實作 agent。你的工作目錄:`{{WORKTREE}}`。

## 任務

依 `examples/shop/spec/` 的 SPEC.md、GLOSSARY.md、ARCHITECTURE.md,在
`examples/shop/app/src/main/java/com/shop/usecase/` 實作**應用層**:
use case、應用側的 port(介面)、view model。命名必須照 GLOSSARY。
`com/shop/domain/` 底下是已完成的領域層原始碼與其測試——**唯讀**,
你要用它、不能改它。

## 邊界(硬規則)

- **你只能寫**:
  - `examples/shop/app/src/main/java/com/shop/usecase/`
  - `examples/shop/app/src/test/java/com/shop/usecase/`(單元測試)
  - `examples/shop/app/ASSUMPTIONS.md`、`examples/shop/app/INTERFACE-REQUESTS.md`
- 工作目錄裡現有的檔案就是你的全部輸入;**不得讀取此 worktree 以外的任何
  路徑**。git 只准用 `status` / `diff` / `add` / `commit`(不得 checkout、
  log、show 其他 branch/commit)。結束時自報你讀過的檔案與跑過的 git 指令。
- 需要白名單以外的任何改動(**含要求 domain 層加方法/建構子**、改 build、
  改 spec):**不得動手、不得繞道**——唯一合法動作是把「要什麼、為什麼」
  寫進 `examples/shop/app/INTERFACE-REQUESTS.md`,commit,停下回報 blocked。

## 工作方式

- usecase 層不 import 框架、不 import adapter(ArchUnit 會抓)。
- **每個 use case 都要有單元測試**(依賴以 test double 替身)。
- 在 `examples/shop/app/` 跑 `./gradlew test` 驗證;完成定義:**全綠**
  (你的+domain 的單元測試 + ArchitectureTest)。
- 規格有歧義:自己決定、不要問人,逐條記 `ASSUMPTIONS.md`。
- 完成(或 blocked)後:`git add` 白名單內你動過的檔案,commit
  (訊息前綴 `impl(usecase):`),回報:測試結果摘要、主要設計決定、
  ASSUMPTIONS 條數、讀檔與 git 指令自報。
