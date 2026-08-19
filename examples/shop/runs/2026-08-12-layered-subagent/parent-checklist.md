# Parent 收件 checklist(每包收件逐條打勾;凍結於開跑前)

每層 agent 交件時,parent 依序:

1. **驗 commit 祖先**:`git log --oneline <setup>..<head>` 全部為該 agent 的
   `impl(<層>):` commit;head 的祖先鏈含 setup commit。
2. **白名單 diff 檢查**(機械,第 2 階):
   `git diff --name-only <setup>..<head>` 逐條對白名單
   (pre-registration 配給表);白名單外路徑非空 = **整包退件**,
   記錄後令其重做,退件次數入報告。
3. **INTERFACE-REQUESTS 檢查**:若存在,先裁決(駁回給替代做法 /
   開票給擁有層),裁決文字留檔於 `arbitration.md`;裁決前不收件。
4. **Parent 親跑測試**:在該 worktree `./gradlew test`,結果以 parent 執行
   為準,不採信自報;記錄綠/紅與紅的科目。
5. **讀檔自報審計**:比對自報讀檔清單與配給——出現配給外路徑 = 記錄
   (榮譽制殘餘,照實入報告)。收件同時把該層的 `ASSUMPTIONS.md` /
   `INTERFACE-REQUESTS.md`(若有)複製進 run 目錄改名
   `ASSUMPTIONS-<樣本>-<層>.md` 等——**.md 記錄檔只收進 run 目錄,
   永不安裝進下游 worktree**(各層白名單都含 `app/ASSUMPTIONS.md`,
   直接 checkout 會把上游記錄併給下游改寫)。
6. usecase 收件後:把 domain 產出安裝進 usecase worktree,**只裝 source:**
   `git checkout <domain分支> -- 'app/src/main/java/com/shop/domain/'
   'app/src/test/java/com/shop/domain/'` + commit `setup: 安裝 domain 產出`,
   不讓 agent 自取。adapter 同理安裝內兩層 source。
7. **整合**:`layered/<樣本>-integration` worktree(不裁檔),依層只
   checkout source 目錄(+adapter 的 `resources/`)、commit、
   `./gradlew test` 全套。紅燈:判歸屬層,失敗輸出原文發回該層 agent
   (SendMessage 續跑原 agent;每層最多 2 輪),仍紅 = 樣本記失敗原樣入報告。
8. **每批收完跑鐵律檢查**:主 worktree `git status --porcelain` 應為空
   (防 subagent 忘 cd、把相對路徑寫進主 worktree——白名單 diff 只審
   agent 自己的 branch,看不到這種)。
9. **記錄表**(每樣本):model、agentId(修復輪 SendMessage 要用)、各層
   耗時/token、退件次數、修復輪數、INTERFACE-REQUESTS 條目與裁決、
   整合測試結果。
