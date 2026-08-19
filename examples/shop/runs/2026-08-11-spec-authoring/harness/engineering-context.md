# 工程前提(三臂逐字相同的受控變因)

- 技術棧已定:Java 17、Spring Boot、Spring Data JPA、H2、Gradle。
- 公司有常備模板(starter):三層 package 佈局 `domain/ usecase/ adapter/`、
  四條通用 ArchUnit 規則(domain 不 import 框架、usecase 不 import 框架、
  domain 不 import 上層、usecase 不 import adapter)、鎖死依賴的 build。
- 你產出的規格文件,讀者是一個 AI 實作 agent;實作的驗收方式是自動化測試。
- 所有文件用繁體中文書寫,技術術語保留英文。
