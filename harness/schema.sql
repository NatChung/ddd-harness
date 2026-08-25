-- harness spec store —— 結構化規則的唯一真相
--
-- 這個檔案是第 1 階(第 9 課階梯):**填不了就寫不進去**。
-- 每一條 CHECK / REFERENCES / TRIGGER 都取代了散文裡的一句叮嚀,
-- 而那句叮嚀必須從 prompt 裡刪掉 —— 兩份規則會漂。
--
-- 對照(散文 → 這裡):
--   「查無來源的 = 捏造,不得存在」          → provenance_ref NOT NULL
--   「來源標記五格,不得自創第六格」          → provenance CHECK IN (...)
--   「嚴禁把本案自決偽裝成模板既定」          → TRIGGER + authorized_template 白名單
--   「無機械檢查要寫明(第 4 階)」            → ladder_note 的條件式 CHECK
--   「由誰強制:指名那條機械檢查」            → enforced_by,只由生成器回填

PRAGMA foreign_keys = ON;

-- 被授權為「架構模板」的文件白名單。
-- **空表 = 模板既定 物理上不可能。** 本案(shop)沒有授權模板文件,所以這張表是空的
-- —— 而歷史上模型兩輪都把自決偽裝成既定,那條規則靠自覺守不住。
CREATE TABLE authorized_template (
    document TEXT PRIMARY KEY
);

CREATE TABLE architecture_rule (
    -- A1, A2, … 生成順序由此決定(排序穩定 → 生成物可 diff)
    id             TEXT PRIMARY KEY,

    -- 一句話,可判定
    rule           TEXT NOT NULL CHECK (length(trim(rule)) > 0),

    -- 五格來源標記。第六格寫不進來。
    provenance     TEXT NOT NULL CHECK (provenance IN
                       ('Qn', '暫定', '推導自', '模板既定', '本案自決')),

    -- [Q3] / 文件名 L行號 / 自決的依據。空的寫不進來。
    provenance_ref TEXT NOT NULL CHECK (length(trim(provenance_ref)) > 0),

    -- 哪個生成器負責把這條變成機械檢查。'none' = 目前只住第 4 階。
    enforcement    TEXT NOT NULL CHECK (enforcement IN
                       ('archunit_forbidden_dependency',
                        'archunit_forbidden_annotation',
                        'archunit_forbidden_return_type',
                        'none')),

    -- enforcement='none' 時必填:為什麼還沒搬上去、搬得上去的話搬去哪。
    -- 這一欄就是「搬階清單」的原料。
    ladder_note    TEXT,

    -- 由生成器回填的機械檢查名(例:ArchitectureTest.rule_A1)。
    -- agent 不得自己寫 —— import 會拒收。
    enforced_by    TEXT,

    CHECK (enforcement <> 'none'
           OR (ladder_note IS NOT NULL AND length(trim(ladder_note)) > 0))
);

-- 「模板既定」必須指向白名單裡的文件。白名單空的話這個 trigger 一定 ABORT。
CREATE TRIGGER template_provenance_must_be_authorized
BEFORE INSERT ON architecture_rule
WHEN NEW.provenance = '模板既定'
BEGIN
    SELECT RAISE(ABORT,
        'provenance 模板既定 必須指向 authorized_template 白名單裡的文件;'
        || '本案無授權架構模板 → 一律用 本案自決')
    WHERE NOT EXISTS (
        SELECT 1 FROM authorized_template
        WHERE NEW.provenance_ref LIKE document || '%'
    );
END;

-- archunit_forbidden_dependency 這個 kind 的參數:一條規則 = 一個來源 package
-- 加一到多個禁止依賴的目標 package。
CREATE TABLE forbidden_dependency (
    rule_id      TEXT NOT NULL REFERENCES architecture_rule(id) ON DELETE CASCADE,

    -- ArchUnit 的 package pattern 必須以 '..' 結尾。打錯寫不進來。
    from_package TEXT NOT NULL CHECK (from_package LIKE '%..'),
    to_package   TEXT NOT NULL CHECK (to_package LIKE '%..'),

    seq          INTEGER NOT NULL,

    PRIMARY KEY (rule_id, to_package)
);

-- archunit_forbidden_annotation 的參數:某個 package 底下的類別(含其欄位、方法、
-- 建構子)不得掛任何來自這些 package 的 annotation。
--
-- 為什麼跟 forbidden_dependency 分開一張表:它們是不同的 kind,參數不同、CHECK 不同。
-- 塞成一張表加一個 kind 欄位,就得把 CHECK 寫成條件式 —— 那是「schema 表達不了」的開端。
--
-- 為什麼需要這一條(A1 已經擋了 import 框架):**A1 擋不到「用對詞掛錯東西」。**
-- annotation 是 import 的一種,但一個類別可以 import jakarta.persistence 卻不掛;
-- 也可以掛了之後靠 fully-qualified 名稱而看起來沒 import。這條直接查 annotation 本身。
CREATE TABLE forbidden_annotation (
    rule_id            TEXT NOT NULL REFERENCES architecture_rule(id) ON DELETE CASCADE,

    from_package       TEXT NOT NULL CHECK (from_package LIKE '%..'),
    annotation_package TEXT NOT NULL CHECK (annotation_package LIKE '%..'),

    seq                INTEGER NOT NULL,

    PRIMARY KEY (rule_id, annotation_package)
);

-- archunit_forbidden_return_type 的參數:某個 package 底下、類名以某個字尾結束的
-- 類別,其 public 方法不得回傳這些 package 的型別。
--
-- 為什麼需要 class_name_suffix:**不能整個 adapter 層都禁**。JpaOrderRepository
-- 住在 adapter,而它本來就該回傳 Order —— 那是它的工作。這條規則只針對 Controller。
-- 這也是這個 kind 跟前兩個的差別:前兩個的 from 是 package,這個的 from 是
-- 「package × 類名形狀」。
CREATE TABLE forbidden_return_type (
    rule_id           TEXT NOT NULL REFERENCES architecture_rule(id) ON DELETE CASCADE,

    from_package      TEXT NOT NULL CHECK (from_package LIKE '%..'),
    class_name_suffix TEXT NOT NULL CHECK (length(trim(class_name_suffix)) > 0),
    return_package    TEXT NOT NULL CHECK (return_package LIKE '%..'),

    seq               INTEGER NOT NULL,

    PRIMARY KEY (rule_id, return_package)
);

-- ─────────────────────────────────────────────────────────────────────────
-- 驗收情境(GWT)—— 第二個生成器的來源
--
-- 這一段比架構規則難的地方是**測試資料**:散文裡的「2 件、單價 1500、TWD」
-- 要變成 fixture。schema 在這裡做的事,是讓寫不出來的資料寫不進去
-- (數量非正、金額為負、幣別不是三碼),而那些在散文裡只能靠讀的人看出來。

-- ⬇⬇ wire shape(ADR 0004)⬇⬇
--
-- 2026-08-18 量到:生成的驗收對凍結的 app 0/4 綠,**每一條的紅都是欄位名對不上**,
-- 沒有一條是領域行為不合。而生成器兩側是非對稱的 —— 請求那半寫死在樣板裡、
-- 回應那半是自由文字。兩側都沒有被宣告,只是一邊寫死、一邊放任。
--
-- 定案:**wire shape 歸規格擁有。** 規格自決之後必須逐欄寫成合約,實作照做。
-- 理由是 MISSION 那條直接要求的:「拿同一份規格餵給兩個不同的 model,兩邊的實作
-- 都能被**同一套驗收**明確判定」—— wire shape 不由規格固定,兩個模型會各取各的
-- 欄位名,**兩邊都不會過**,那套驗收就判定不了任何事。
--
-- ⚠️ 這張表擋得住的是**內部不一致**(斷言引用了沒宣告的欄位),
--    擋不住**跟實際 app 的分歧** —— 後者不是 schema 能擋的,那是實作要照合約做。
--    別把這張表讀成「欄位名對不對」的保證。

CREATE TABLE wire_contract (
    -- 一份 spec 綁一份合約。CHECK 讓第二份寫不進來。
    id                INTEGER PRIMARY KEY CHECK (id = 1),
    name              TEXT NOT NULL CHECK (length(trim(name)) > 0),

    -- 請求那側(舊版寫死在 gen_acceptance.py 的樣板裡)
    req_customer_field TEXT NOT NULL,
    req_items_field    TEXT NOT NULL,
    req_product_field  TEXT NOT NULL,
    req_quantity_field TEXT NOT NULL,
    req_price_field    TEXT NOT NULL,
    req_currency_field TEXT NOT NULL,
    -- 請求夾帶總金額用的欄位名(S3)。NULL = 這份合約沒有這個欄位。
    req_total_field    TEXT,

    -- 回應那側
    res_order_id_field TEXT NOT NULL,   -- POST 回應與列表一列共用的訂單識別欄
    -- 列表一列裡的總金額欄。**Σ(數量 × 單價) 那條不變式靠它認人。**
    -- ⚠️ 2026-08-18:這一欄的名字原本寫死在 spec_store 裡。
    --    欄位名改歸合約擁有之後,規格只要取別的名字,
    --    那條不變式就**靜靜地永遠不再檢查** —— 守衛沒有壞掉,是不再適用了,
    --    而不適用不會有人發現。守衛的「認人方式」跟著合約走,才不會這樣失效。
    res_total_field    TEXT,
    -- 列表一列裡的客人編號欄。NULL = 這份合約**不揭露**客人編號,
    -- 因此用不了 list_no_row_for_customer。這不是缺陷,是合約的事實。
    res_customer_id_field TEXT
);

-- 列表一列有哪些欄位。scenario_assertion.field FK 指這裡 ——
-- 斷言引用沒宣告的欄位就 import 不進去。
CREATE TABLE wire_list_field (
    field TEXT PRIMARY KEY
);

CREATE TABLE acceptance_scenario (
    id             TEXT PRIMARY KEY,
    given_when     TEXT NOT NULL CHECK (length(trim(given_when)) > 0),
    then_expect    TEXT NOT NULL CHECK (length(trim(then_expect)) > 0),
    provenance     TEXT NOT NULL CHECK (provenance IN
                       ('Qn', '暫定', '推導自', '模板既定', '本案自決')),
    provenance_ref TEXT NOT NULL CHECK (length(trim(provenance_ref)) > 0),

    -- 這個情境預期請求被拒嗎?見 ADR 0003。
    -- 它不只是個註記 —— 底下的 UNIQUE 讓它變成 rejected_request 那組表的鑰匙:
    -- **只有 expects_rejection=1 的情境,掛得上違法的 fixture。**
    expects_rejection INTEGER NOT NULL DEFAULT 0
                          CHECK (expects_rejection IN (0, 1)),

    -- 代理編碼的自白。fixture 若不包含 given_when 描述的那個動作,必填。
    -- 見 ADR 0004 的鄰居討論與 CONTEXT.md「代理編碼」。
    -- ⚠️ 這**不是偵測器** —— 它擋不住存心不填的人。它買的是:誠實的情況變成
    --    查得出來的欄位(SELECT ... WHERE proxy_for IS NOT NULL 就是分診佇列),
    --    而不是躺在註解裡靠人讀到。實測過一次:agent 自願揭露了 S10 是代理編碼,
    --    但自願的東西換個模型就沒了。
    proxy_for      TEXT,

    -- 這一對是子表 FK 的目標。沒有它,「違法 fixture 只能掛在預期被拒的情境上」
    -- 就只能寫成條件式 CHECK —— 而 L88 那條註解說過那是什麼的開端。
    UNIQUE (id, expects_rejection)
);

-- 「模板既定」必須指向白名單裡的文件 —— 這張表原本沒掛,而規則對它一樣適用。
-- 白名單空的話這個 trigger 一定 ABORT。
CREATE TRIGGER scenario_template_provenance_must_be_authorized
BEFORE INSERT ON acceptance_scenario
WHEN NEW.provenance = '模板既定'
BEGIN
    SELECT RAISE(ABORT,
        'provenance 模板既定 必須指向 authorized_template 白名單裡的文件;'
        || '本案無授權架構模板 → 一律用 本案自決')
    WHERE NOT EXISTS (
        SELECT 1 FROM authorized_template
        WHERE NEW.provenance_ref LIKE document || '%'
    );
END;

-- 一個情境裡送出的每一筆訂單。alias 讓後面的斷言指得到是哪一筆
-- (一個情境可能要送多筆才證明得了事情 —— 例如「姓名是 join 出來的、不是寫死的」,
--  一筆訂單證明不了)。
--
-- ⚠️ 註解不要寫具體資料值。2026-08-18 這裡曾舉過兩個人名當例子,其中一個只存在於
--    agent 拿不到的測試資料檔;受測 agent 讀了這行註解、照著填,並誠實揭露來源。
--    **schema 註解是 agent 讀得到的東西,寫進去的具體值就是洩題。**
--    2026-08-19 補:那句警語**自己把那兩個名字寫在裡面**,所以它自己就是洩題源。
--    講失效模式不需要舉實際的值 —— 舉了就等於把答案附在警語後面。
CREATE TABLE scenario_step (
    scenario_id TEXT NOT NULL REFERENCES acceptance_scenario(id) ON DELETE CASCADE,
    alias       TEXT NOT NULL CHECK (alias GLOB '[a-z][a-zA-Z0-9_]*'),  -- 要當 Java 變數名
    seq         INTEGER NOT NULL,
    customer_id TEXT NOT NULL CHECK (length(trim(customer_id)) > 0),

    -- 請求裡夾帶的總金額。領域**沒有**這個概念 —— 系統必須忽略它、自己算。
    -- NULL = 沒夾帶。
    --
    -- ⚠️ 這一欄住在「領域值」的表裡,是刻意的例外,理由要記著:
    --    S3「總金額不接受人為指定」預期的是**成立**(201、總額仍是算出來的),
    --    不是被拒 —— 所以它掛不到 rejected_request 上。而要證明「指定值被忽略」,
    --    唯一的辦法就是**真的送一個進去**。
    --    2026-08-18 第一次寫這組表時漏了這一欄,把 S3 誤當成拒絕情境 ——
    --    是照真實規格造測試資料時才發現的,不是想出來的。
    claimed_total_cents INTEGER,

    PRIMARY KEY (scenario_id, alias)
);

CREATE TABLE step_item (
    scenario_id      TEXT NOT NULL,
    alias            TEXT NOT NULL,
    seq              INTEGER NOT NULL,
    product_id       TEXT    NOT NULL CHECK (length(trim(product_id)) > 0),
    quantity         INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_cents INTEGER NOT NULL CHECK (unit_price_cents >= 0),
    currency         TEXT    NOT NULL CHECK (length(currency) = 3),
    PRIMARY KEY (scenario_id, alias, seq),
    FOREIGN KEY (scenario_id, alias)
        REFERENCES scenario_step(scenario_id, alias) ON DELETE CASCADE
);

-- ⬇⬇ 負面情境的 fixture(ADR 0003)⬇⬇
--
-- 為什麼另開一組表,而不是放寬 step_item 的 CHECK:
-- **step_item 存的是領域值,這裡存的是請求。** 客戶端可以送數量 0、送空單、
-- 沒登入;領域一個都不能持有。同一張表兼差兩者,CHECK 就得寫成條件式(見 L88)。
--
-- 為什麼欄位重複一份而不共用:重複是刻意付的代價,換「不寫條件式 CHECK」。
--
-- ⚠️ expects_rejection 掛在**情境**上,所以一個情境不能同時有「成功的前置訂單」
--    與「被拒的請求」。S8(既有訂單 → 改它 → 拒絕)那種混合情境目前表達不了 ——
--    那屬於「動詞不夠」那一類,做那類的時候要重審 ADR 0003。

CREATE TABLE rejected_request (
    scenario_id       TEXT NOT NULL,
    -- 恆為 1。它跟 FK 一起,把「只有預期被拒的情境掛得上」變成宣告式的。
    expects_rejection INTEGER NOT NULL CHECK (expects_rejection = 1),
    alias             TEXT NOT NULL CHECK (alias GLOB '[a-z][a-zA-Z0-9_]*'),
    seq               INTEGER NOT NULL,

    -- ⚠️ 這裡**刻意沒有** length(trim(customer_id)) > 0 —— S7「未登入者下單」
    --    要送得出空的下單者。領域擋得住,請求擋不住,這張表存的是後者。
    customer_id       TEXT NOT NULL,

    -- 請求裡夾帶的總金額(S3)。領域沒有這個概念 —— 系統必須忽略它。
    -- NULL = 沒夾帶。這就是 ADR 0003 說 S3 是特例的那一欄:它要的不是放寬約束,
    -- 是多一個領域模型裡不存在的欄位。
    claimed_total_cents INTEGER,

    PRIMARY KEY (scenario_id, alias),
    FOREIGN KEY (scenario_id, expects_rejection)
        REFERENCES acceptance_scenario(id, expects_rejection) ON DELETE CASCADE
);

-- 違法的明細。**一條 CHECK 都沒有**,而那正是它跟 step_item 的差別。
-- S4(空單)靠「一筆 rejected_request 可以沒有任何 rejected_request_item」表達 ——
-- 所以 importer 那邊也不准要求它非空(舊版 spec_store.py:227 就是那樣擋掉 S4 的)。
CREATE TABLE rejected_request_item (
    scenario_id      TEXT    NOT NULL,
    alias            TEXT    NOT NULL,
    seq              INTEGER NOT NULL,
    product_id       TEXT    NOT NULL,
    quantity         INTEGER NOT NULL,   -- 沒有 > 0:S5 送 0、S6 送 -1
    unit_price_cents INTEGER NOT NULL,   -- 沒有 >= 0
    currency         TEXT    NOT NULL,   -- 沒有 length = 3
    PRIMARY KEY (scenario_id, alias, seq),
    FOREIGN KEY (scenario_id, alias)
        REFERENCES rejected_request(scenario_id, alias) ON DELETE CASCADE
);

-- 斷言。kind ↔ 該帶哪些參數,寫死在 CHECK 裡 ——
-- 「status_is 卻給了 field」「list_field_equals_text 卻沒給期望值」都寫不進去。
CREATE TABLE scenario_assertion (
    scenario_id     TEXT NOT NULL REFERENCES acceptance_scenario(id) ON DELETE CASCADE,
    seq             INTEGER NOT NULL,
    kind            TEXT NOT NULL CHECK (kind IN (
                        'status_is',
                        'order_id_not_blank',
                        'list_row_exists',
                        'list_field_equals_text',
                        'list_field_equals_number',
                        'list_field_is_iso_date')),
    target_alias    TEXT NOT NULL,
    -- 引用列表一列的哪個欄位。FK 讓「斷言了一個沒宣告的欄位」寫不進來(ADR 0004)。
    -- 非 list_field_* 的 kind 這裡是 NULL,SQLite 的 FK 放行 NULL。
    field           TEXT REFERENCES wire_list_field(field),
    expected_text   TEXT,
    expected_number INTEGER,

    PRIMARY KEY (scenario_id, seq),
    FOREIGN KEY (scenario_id, target_alias)
        REFERENCES scenario_step(scenario_id, alias) ON DELETE CASCADE,

    CHECK (
        (kind = 'status_is'
             AND field IS NULL AND expected_text IS NULL AND expected_number IS NOT NULL)
     OR (kind IN ('order_id_not_blank', 'list_row_exists')
             AND field IS NULL AND expected_text IS NULL AND expected_number IS NULL)
     OR (kind = 'list_field_equals_text'
             AND field IS NOT NULL AND expected_text IS NOT NULL AND expected_number IS NULL)
     OR (kind = 'list_field_equals_number'
             AND field IS NOT NULL AND expected_number IS NOT NULL AND expected_text IS NULL)
     OR (kind = 'list_field_is_iso_date'
             AND field IS NOT NULL AND expected_text IS NULL AND expected_number IS NULL)
    )
);

-- 負面情境的斷言(ADR 0003)。
--
-- 為什麼不塞進 scenario_assertion:那張表的 target_alias FK 指 scenario_step,
-- 而負面情境的目標是 rejected_request。一個 FK 指不到兩張表,而**放棄那個 FK**
-- 等於放棄「斷言指向不存在的 alias 會被擋下」這個守衛 —— 那是真的會發生的打字錯。
--
-- 分開之後多買到一件事:**正面情境用不到負面的 kind,反之亦然**,
-- 而那是 schema 擋得住的,不用寫檢查。
CREATE TABLE rejected_assertion (
    scenario_id     TEXT NOT NULL,
    seq             INTEGER NOT NULL,
    kind            TEXT NOT NULL CHECK (kind IN (
                        -- 請求被拒:400 / 401 …
                        'status_is',
                        -- 列表裡沒有任何一列屬於這個請求的客人編號。
                        -- ⚠️ 名字刻意寫成 _for_customer 而不是 order_not_created ——
                        --    **比對的鍵是客人編號**,把比對方式寫進 kind 名字,誤用才看得見。
                        'list_no_row_for_customer')),
    target_alias    TEXT NOT NULL,
    expected_number INTEGER,

    PRIMARY KEY (scenario_id, seq),
    FOREIGN KEY (scenario_id, target_alias)
        REFERENCES rejected_request(scenario_id, alias) ON DELETE CASCADE,

    CHECK (
        (kind = 'status_is' AND expected_number IS NOT NULL)
     OR (kind = 'list_no_row_for_customer' AND expected_number IS NULL)
    )
);

-- ─────────────────────────────────────────────────────────────────────────
-- 領域契約(§3 Design by Contract)—— 微尺度
--
-- 大尺度有 architecture_rule(配了一支生成器),小尺度有 wire_contract
-- (生成器兩側都讀它),**微尺度在這張表出現之前一張表都沒有**。於是一條 invariant
-- 進得了 store 的唯一形式,是被寫成某一條情境的斷言 —— 規格說「任何時候都成立」,
-- 而驗收只證明了「其中一筆成立」。**invariant 被降級成 example。**
--
-- ⚠️ 這張表**不生成任何可執行的東西**。它買的是兩件事:
--    (1)「這條契約有沒有指名測試」變成一句 SELECT;
--    (2)「守不住的契約」變成分診佇列,而不是靠人讀散文裡的驚嘆號。
--    契約表達不出來的時候,**要讓它顯眼地表達不出來** —— 不得為了讓它「有機械檢查」
--    而把它塞成一條情境,那是 proxy_for 那個病。

CREATE TABLE domain_contract (
    -- C1, C2, … 排序穩定 → 報表可 diff
    id TEXT PRIMARY KEY,

    -- 契約三型。散文有時在型態後面加括號註記(哪一類失敗、讀取面),
    -- 那是 statement 的一部分,不得拿來擴充這裡的值域。
    kind TEXT NOT NULL CHECK (kind IN ('precondition', 'postcondition', 'invariant')),

    -- 一句話,可判定
    statement TEXT NOT NULL CHECK (length(trim(statement)) > 0),

    -- 五格來源標記,與 architecture_rule / acceptance_scenario **逐字相同**。
    -- 第六格寫不進來,也不得為新表改格名 —— 同一條規則寫在多個地方會漂。
    provenance TEXT NOT NULL CHECK (provenance IN
                   ('Qn', '暫定', '推導自', '模板既定', '本案自決')),
    provenance_ref TEXT NOT NULL CHECK (length(trim(provenance_ref)) > 0),

    -- 守在哪個物件內。**刻意不叫「聚合根」** —— 有的契約守的是 Value Object 自身,
    -- 而 Value Object 不是聚合根;舊欄名跟裝得進來的東西對不上。
    guarded_in TEXT NOT NULL CHECK (length(trim(guarded_in)) > 0),

    -- 判定這條需不需要看守衛物件以外的資料。1 = 它在那個物件內守不住。
    -- ⚠️ 這一欄記的是**規格標了什麼**,不是重新判定的結果。散文漏標的,這裡一樣漏。
    crosses_aggregate INTEGER NOT NULL DEFAULT 0 CHECK (crosses_aggregate IN (0, 1)),

    -- 旗標 = 1 時必填,而且**存本文,不存指標**。「見某某節」會製造本線最常見的那條病:
    -- **寫在該寫的地方 ≠ 接上了** —— 指過去了,而下游沒有任何一步會去讀那一節。
    -- (「只寫指標」的幾種寫法認得出來,擋在 spec_store.py 的第 2 階。)
    disposition TEXT,

    -- 哪個生成器負責把這條變成機械檢查。
    -- ⚠️ 值域今天只有 'none',**因為今天沒有任何生成器讀這張表**。照抄
    --    architecture_rule 的 kind 清單,會讓一條契約宣稱一個沒有人履行的檢查
    --    —— 那幾個 kind 的參數子表全部 FK 指向 architecture_rule。
    --    這是**今天的值域,不是定義**:結構型契約的生成器落地時才擴。
    enforcement TEXT NOT NULL CHECK (enforcement IN ('none')),

    -- enforcement='none' 時必填:為什麼還住第 4 階、搬得上去的話搬去哪。
    -- 這一欄就是「搬階清單」的原料。
    ladder_note TEXT,

    -- 由生成器回填的機械檢查名。agent 不得自己寫 —— import 會拒收。
    enforced_by TEXT,

    -- 一條契約在 contract_named_test 裡零列時,必須說出為什麼指不出來。
    -- ⚠️ 「零列時必填」這條 **CHECK 寫不出來**(要跨表數列),它住 spec_store.py 的
    --    **第 2 階**,不是第 1 階。零列跟「還沒填」長得一模一樣,所以要逼出理由。
    no_named_test_reason TEXT,

    CHECK (crosses_aggregate = 0
           OR (disposition IS NOT NULL AND length(trim(disposition)) > 0)),
    CHECK (enforcement <> 'none'
           OR (ladder_note IS NOT NULL AND length(trim(ladder_note)) > 0))
);

-- 「模板既定」必須指向白名單裡的文件。白名單空的話這個 trigger 一定 ABORT。
CREATE TRIGGER contract_template_provenance_must_be_authorized
BEFORE INSERT ON domain_contract
WHEN NEW.provenance = '模板既定'
BEGIN
    SELECT RAISE(ABORT,
        'provenance 模板既定 必須指向 authorized_template 白名單裡的文件;'
        || '本案無授權架構模板 → 一律用 本案自決')
    WHERE NOT EXISTS (
        SELECT 1 FROM authorized_template
        WHERE NEW.provenance_ref LIKE document || '%'
    );
END;

-- 「指名測試」—— 一張關聯表,不是一格自由文字。
-- 指向一個不存在的情境編號(打字錯)**寫不進去**,那是第 1 階。
--
-- ⚠️ **這張表跟 domain_contract.enforcement 是兩件事,不得合併。**
--    一條契約可以指名好幾個情境、看起來「有人在守」,而那些情境各自只證明了自己那一筆;
--    契約說的是「任何時候」。把「有指名測試」算成「有機械檢查」,
--    就把 invariant → example 的降級整個蓋住 —— 而那正是這組表要抓的東西。
--
-- ⚠️ 今天指得到的只有驗收情境。那是**今天的值域,不是這一欄的定義** ——
--    日後別種測試也會是候選,不要把語意讀死成「指名測試 = 驗收情境」。
CREATE TABLE contract_named_test (
    contract_id TEXT NOT NULL REFERENCES domain_contract(id) ON DELETE CASCADE,
    scenario_id TEXT NOT NULL REFERENCES acceptance_scenario(id) ON DELETE CASCADE,

    -- 散文列出來的順序。排序穩定 → 報表可 diff。
    seq         INTEGER NOT NULL,

    PRIMARY KEY (contract_id, scenario_id)
);

-- ─────────────────────────────────────────────────────────────────────────
-- 詞彙表(§1 GLOSSARY)—— ubiquitous language 的載體
--
-- `GLOSSARY` 是節名;**ubiquitous language 是那份表要達成的性質** ——
-- 一份詞彙表只有在**每一處都照它**的時候才叫 ubiquitous,沒有人遵守就只是一份 glossary。
-- 這張表出現之前,詞彙表只活在散文裡:規格層寫著「實作命名必須照此表」,
-- 而**沒有任何一步會去讀那句話**。
--
-- ⚠️ 這張表**不生成任何可執行的東西**,也**不檢查實作的類別 / 方法 / 變數名**
--    —— 那要靠一種命名類的規則,而那個判定還沒拍板。這裡買到的只有一件事:
--    「對外欄位名有沒有對得到一個詞」從**自律**變成**查得出來的差額**。
--
-- ⚠️ 對譯檢查**刻意不做成 FK**。硬擋只拿得到「匯入失敗」,拿不到「差幾個、差哪幾個」,
--    而那個差額才是這張表要買的東西。檢查住 glossary_check.py 的**第 2 階報告**。

CREATE TABLE glossary_term (
    -- 散文那一格的原文。可能是中文、英文,或中英並列 —— **原樣存**。
    -- ⚠️ 刻意不另開一欄裝「實作類別名」:那是實作層的命名,而實作層要不要被約束
    --    還沒拍板。多開那一欄等於先替那個判定投了票。
    term TEXT PRIMARY KEY,

    definition TEXT NOT NULL CHECK (length(trim(definition)) > 0),

    -- DDD 型態。**自由文字,刻意不做成固定清單。**
    -- ⚠️ 這一欄只住**第 4 階**(規格層讀得懂,沒有任何機械檢查看它)。
    --    查過兩份真實詞彙表之後放棄鎖清單:它們的型態用語幾乎不重疊,
    --    鎖清單會逼下一份詞彙表把自己的詞硬塞進別人的格子 ——
    --    **那會製造假資料,不是擋假資料**。累積到看得見真正的值域再走搬階。
    ddd_type TEXT NOT NULL CHECK (length(trim(ddd_type)) > 0),

    -- 單位 / 表示法。可空:很多詞沒有單位,而散文那一格就是空的。
    representation TEXT,

    -- 對外欄位名(這個詞在 API 上叫什麼)。
    -- ⚠️ **可空,而空白有語意:這個詞不上線,不是漏填。** 界外系統、只在說明裡出現的
    --    角色,本來就不會有欄位名。
    -- ⚠️ 但空白裝得下的不只一種情況(見 glossary_check.py 的上限):
    --    真的不上線 / 散文那一格寫的不是一個欄位名 / 這份詞彙表根本沒有這一欄。
    --    **計數分不開這三種**,所以報表逐個印,不只印數量。
    -- UNIQUE:兩個詞宣稱同一個對外欄位名 = 對譯有歧義,寫不進來。
    --    (SQLite 的 UNIQUE 放行多個 NULL,所以「不上線」的詞不受影響。)
    wire_field TEXT UNIQUE,

    -- 五格來源標記,與 architecture_rule / acceptance_scenario / domain_contract
    -- **逐字相同**。第六格寫不進來,也不得為新表改格名。
    provenance TEXT NOT NULL CHECK (provenance IN
                   ('Qn', '暫定', '推導自', '模板既定', '本案自決')),
    provenance_ref TEXT NOT NULL CHECK (length(trim(provenance_ref)) > 0),

    -- 散文列出來的順序。排序穩定 → 報表可 diff(照 term 排會被語言的排序規則牽著走)。
    seq INTEGER NOT NULL
);

-- 「模板既定」必須指向白名單裡的文件。白名單空的話這個 trigger 一定 ABORT。
CREATE TRIGGER glossary_template_provenance_must_be_authorized
BEFORE INSERT ON glossary_term
WHEN NEW.provenance = '模板既定'
BEGIN
    SELECT RAISE(ABORT,
        'provenance 模板既定 必須指向 authorized_template 白名單裡的文件;'
        || '本案無授權架構模板 → 一律用 本案自決')
    WHERE NOT EXISTS (
        SELECT 1 FROM authorized_template
        WHERE NEW.provenance_ref LIKE document || '%'
    );
END;

-- 禁用同義詞 —— **另開子表,因為一個詞擋得掉好幾種講法**(一對多)。
-- 散文常把好幾種講法擠在同一格,擠在一起就只能靠人讀;拆開之後它是一句 SELECT。
--
-- ⚠️ **這不是第四個 ArchUnit rule kind。** 這張表**不掃任何識別字** ——
--    英文字根會撞(同一個字根出現在兩種識別字裡都可能是對的),
--    掃出來的東西會**懲罰寫得好的那一方**。這裡只買「查得到的清單」,不買判決。
CREATE TABLE glossary_banned_synonym (
    -- 禁止裸用的那個講法。一列一個講法。
    banned TEXT PRIMARY KEY,

    -- 一律改用哪個詞。**FK 指回 glossary_term** —— 叫人改用一個詞彙表裡不存在的詞,
    -- 寫不進來(那是真的會發生的,而散文自己看不出來)。
    -- NULL = 這個講法**沒有替代詞**(它指的東西在本案根本不存在)。
    use_instead TEXT REFERENCES glossary_term(term),

    -- use_instead 為 NULL 時必填:為什麼沒有替代詞。
    -- 「真的沒有替代詞」與「還沒填」長得一模一樣,所以要逼出理由。
    no_replacement_note TEXT,

    -- 散文那一列除了「禁詞」「一律改用」之外多出來的那一格,**逐字裝**。
    -- ⚠️ 刻意只有一格、而且刻意**不給這張子表自己的五格來源標記**:
    --    查過的兩份真實清單**欄位不一樣**(一份有「為什麼」沒有來源,另一份反過來)。
    --    硬要兩格、或硬要五格,就會逼其中一份憑空生出它沒有的東西 ——
    --    跟鎖 ddd_type 清單同一個病,只是換成**欄位存在性**而不是值域。
    note TEXT NOT NULL CHECK (length(trim(note)) > 0),

    seq INTEGER NOT NULL,

    CHECK (use_instead IS NOT NULL
           OR (no_replacement_note IS NOT NULL
               AND length(trim(no_replacement_note)) > 0))
);
