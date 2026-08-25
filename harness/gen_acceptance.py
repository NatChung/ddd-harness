#!/usr/bin/env python3
"""SQLite store → OrderAcceptanceTest.java(第 3 階的可執行驗收)。

第二個生成器。跟第一個(ARCHITECTURE → ArchUnit)最大的差別是**測試資料**:
架構規則只有 package 名,情境有金額、數量、幣別、期望值 —— 那些要變成 fixture。

生成的驗收**刻意不 import 任何實作類別**(唯一的 com.shop 引用是 Application,
啟動用)。整份只走 HTTP,所以它不綁實作的類名、不綁內部結構
—— 兩份長得完全不同的實作,都能被這同一套驗收明確判定。那是 MISSION 那條
「同一份規格餵兩個 model,能被同一套驗收明確判定」的字面實作。

離開碼:
    0  生成了
    2  用法錯誤(參數個數不對)
    3  **不適用** —— 這份 store 沒有驗收情境,或有情境卻沒宣告 wire shape。
       兩種原因**印出來的話不一樣**(後者是規格缺了一塊,不是「這份沒有驗收」);
       `generate()` 走的是 `NothingToGenerate`,**不是 `SystemExit`** ——
       後者會把 import 它的呼叫方(`verify_generated.py`)整支打死。

用法:
    python3 gen_acceptance.py <spec.db> <out/OrderAcceptanceTest.java>
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from spec_store import NothingToGenerate  # noqa: E402

CLASS_NAME = "OrderAcceptanceTest"
PROXY_CLASS_NAME = "OrderProxyAcceptanceTest"

MAIN_JAVADOC = """/**
 * 生成物 —— 由 harness/gen_acceptance.py 從 spec store 產生。
 *
 * <p><b>不要手改這個檔案。</b>要改情境就改 spec,重新生成;
 * {@code verifyGenerated} 會抓到手改。
 *
 * <p>這裡刻意<b>不 import 任何實作類別</b> —— 唯一引用的 com.shop 類別是
 * harness 自己的 Application(啟動用)。整份驗收只透過 HTTP 進行,所以它
 * 不綁任何實作的類別名稱、不綁任何內部結構。骨架(還沒有任何實作)時它必須是紅的。
 *
 * <p><b>這個 class 全綠 = 驗收通過。</b>代理編碼的情境不在這裡,
 * 在 {@code OrderProxyAcceptanceTest} —— 那些綠了不算數。
 */"""

PROXY_JAVADOC = """/**
 * 生成物 —— <b>代理編碼的情境</b>,由 harness/gen_acceptance.py 產生。
 *
 * <p><b>⚠️ 這個 class 全綠,不代表這些規格條文成立。</b>
 *
 * <p>這裡每一條的 fixture 都<b>不包含它的 Given/When 所描述的那個動作</b>
 * —— schema 沒有那個動詞,所以規格作者用別的東西近似它,並在 {@code proxy_for}
 * 裡自白覆蓋到哪一半。每個測試方法的 javadoc 都帶著那段自白,逐條讀得到。
 *
 * <p>所以它們<b>不可能因為自己宣稱要測的理由而失敗</b>:
 * 「系統寫到一半掛掉,不該留下任何東西」被編成「建一筆訂單,斷言它存在」,
 * 那條綠燈只證明了「建得起來」。
 *
 * <p><b>為什麼還是生出來跑</b>:它們仍然擋得住「連近似的那一半都壞了」,
 * 而且留在這裡才看得見缺口有多大。<b>但不要把它算進驗收</b> ——
 * 驗收看 {@code OrderAcceptanceTest}。真正的修法是補上缺的動詞
 * (見 .scratch/ddd-harness/issues/01),補完這個 class 就會變空。
 */"""

HEADER = '''package acceptance;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

__JAVADOC__
@SpringBootTest(
        classes = com.shop.Application.class,
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@DisplayName("驗收(生成物):下單(Command)與訂單列表(Query)")
class __CLASS_NAME__ {

    @Autowired
    private TestRestTemplate rest;

    private final ObjectMapper mapper = new ObjectMapper();
'''

FOOTER = '''
    // ---------- helpers ----------
    //
    // 欄位名來自 spec 宣告的 wire 合約「__CONTRACT_NAME__」(ADR 0004),
    // 不是生成器寫死的。實作必須照這份合約做。

    private ResponseEntity<String> placeOrder(String json) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        return rest.exchange("/orders", HttpMethod.POST, new HttpEntity<>(json, headers), String.class);
    }

    private String orderIdOf(ResponseEntity<String> res) {
        assertThat(res.getStatusCode().value())
                .as("POST /orders 應回 201,實際 %s,body=%s", res.getStatusCode(), res.getBody())
                .isEqualTo(201);
        try {
            Map<String, Object> body = mapper.readValue(res.getBody(), new TypeReference<>() {});
            Object id = body.get("__ORDER_ID_FIELD__");
            assertThat(id).as("POST /orders 的回應缺少 __ORDER_ID_FIELD__,body=%s", res.getBody()).isNotNull();
            return id.toString();
        } catch (Exception e) {
            throw new AssertionError("POST /orders 的回應不是預期的 JSON:" + res.getBody(), e);
        }
    }

    private List<Map<String, Object>> listRows() {
        ResponseEntity<String> res = rest.getForEntity("/orders", String.class);
        assertThat(res.getStatusCode().value())
                .as("GET /orders 應回 200,實際 %s,body=%s", res.getStatusCode(), res.getBody())
                .isEqualTo(200);
        try {
            return mapper.readValue(res.getBody(), new TypeReference<>() {});
        } catch (Exception e) {
            throw new AssertionError("GET /orders 的回應不是預期的 JSON:" + res.getBody(), e);
        }
    }

    private Map<String, Object> findInList(String orderId) {
        return listRows().stream()
                .filter(r -> orderId.equals(String.valueOf(r.get("__ORDER_ID_FIELD__"))))
                .findFirst()
                .orElse(null);
    }
__CUSTOMER_IDS_HELPER__}
'''

# 只有在合約揭露客人編號時才生得出來。凍結那份合約沒有這一欄,
# 所以它的生成物裡不會有這個 helper —— 而 import 期就已經擋掉用得到它的斷言了。
CUSTOMER_IDS_HELPER = '''
    /** 列表上所有訂單的客人編號。負面情境用它斷言「沒有屬於這個客人的列」。 */
    private List<String> customerIdsInList() {
        return listRows().stream()
                .map(r -> String.valueOf(r.get("__CUSTOMER_ID_FIELD__")))
                .toList();
    }
'''


def _java_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _var(prefix: str, alias: str) -> str:
    return prefix + alias[0].upper() + alias[1:]


def _request_body(wire: sqlite3.Row, customer_id: str, items: list[sqlite3.Row],
                  claimed_total_cents: int | None = None) -> str:
    """組 Java text block 裡的 JSON。縮排寫死,生成物才可 diff。

    ⚠️ **這裡不做任何值的檢查。** 數量 0、負數、空的 items、空的 customerId 都要
    原樣送出去 —— 負面情境要證明的就是「送了這個進去,系統擋下來」。
    生成器若在這裡替它修正,那條驗收就永遠是綠的,而且是假的。

    `claimed_total_cents` 是請求夾帶的總金額(S3):領域沒有這個概念,
    系統必須忽略它、自己算。
    """
    head = (f'                {{"{wire["req_customer_field"]}":'
            f'"{_java_string(customer_id)}"')
    if claimed_total_cents is not None:
        # 刻意放在 items 之前 —— 讓它在 JSON 裡顯眼,讀生成物的人一眼看到夾帶值。
        head += f',"{wire["req_total_field"]}":{claimed_total_cents}'
    items_key = wire["req_items_field"]
    if not items:
        # S4 空單:一項商品都沒有。這是合法的**請求**,不是合法的訂單。
        return head + f',"{items_key}":[]}}'
    lines = [head + f',"{items_key}":[']
    for i, item in enumerate(items):
        comma = "," if i < len(items) - 1 else ""
        lines.append(
            f'                  {{"{wire["req_product_field"]}":'
            f'"{_java_string(item["product_id"])}",'
            f'"{wire["req_quantity_field"]}":{item["quantity"]},'
            f'"{wire["req_price_field"]}":{item["unit_price_cents"]},'
            f'"{wire["req_currency_field"]}":"{_java_string(item["currency"])}"}}{comma}'
        )
    lines.append("                ]}")
    return "\n".join(lines)


def _rejected_assertion_lines(assertion: sqlite3.Row, customer_id: str) -> list[str]:
    """負面情境的斷言(ADR 0003)。

    這裡**不能用** `orderIdOf()` / `findInList()` —— 前者硬斷言 201,後者靠
    orderId 找列,而被拒的請求兩樣都沒有。
    """
    alias = assertion["target_alias"]
    res = _var("res", alias)
    kind = assertion["kind"]
    if kind == "status_is":
        return [
            f"        assertThat({res}.getStatusCode().value())",
            f'                .as("請求應被拒絕,body=%s", {res}.getBody())',
            f"                .isEqualTo({assertion['expected_number']});",
        ]
    if kind == "list_no_row_for_customer":
        return [
            f'        assertThat(customerIdsInList())',
            f'                .as("請求被拒了,列表卻出現屬於這個客人的訂單")',
            f'                .doesNotContain("{_java_string(customer_id)}");',
        ]
    raise SystemExit(f"生成器不認得的 rejected assertion kind:{kind}")


def _assertion_lines(assertion: sqlite3.Row) -> list[str]:
    alias = assertion["target_alias"]
    row, res, oid = _var("row", alias), _var("res", alias), _var("id", alias)
    field = assertion["field"]
    kind = assertion["kind"]
    if kind == "status_is":
        return [
            f"        assertThat({res}.getStatusCode().value())",
            f"                .isEqualTo({assertion['expected_number']});",
        ]
    if kind == "order_id_not_blank":
        return [f"        assertThat({oid}).isNotBlank();"]
    if kind == "list_row_exists":
        return [
            f'        assertThat({row}).as("列表中找不到訂單 %s", {oid}).isNotNull();'
        ]
    if kind == "list_field_equals_text":
        return [
            f'        assertThat({row}.get("{_java_string(field)}"))',
            f'                .isEqualTo("{_java_string(assertion["expected_text"])}");',
        ]
    if kind == "list_field_equals_number":
        return [
            f'        assertThat(((Number) {row}.get("{_java_string(field)}")).longValue())',
            f"                .isEqualTo({assertion['expected_number']}L);",
        ]
    if kind == "list_field_is_iso_date":
        return [
            f'        assertThat({row}.get("{_java_string(field)}")).isNotNull();',
            f'        assertThat(LocalDate.parse({row}.get("{_java_string(field)}").toString()))',
            "                .isNotNull();",
        ]
    raise SystemExit(f"生成器不認得的 assertion kind:{kind}")


def _rejection_scenario(conn: sqlite3.Connection, wire: sqlite3.Row,
                        sc: sqlite3.Row) -> str:
    """負面情境的測試方法(ADR 0003)。

    跟正面情境的差別不只是斷言:**這裡不呼叫 `orderIdOf()`** ——
    它硬斷言 201,對一個預期被拒的請求會在斷言到重點之前就爆掉,
    而爆掉的訊息會說「應回 201」,把真正的失敗蓋掉。
    """
    sid = sc["id"]
    requests = conn.execute(
        "SELECT * FROM rejected_request WHERE scenario_id = ? ORDER BY seq", (sid,)
    ).fetchall()
    assertions = conn.execute(
        "SELECT * FROM rejected_assertion WHERE scenario_id = ? ORDER BY seq", (sid,)
    ).fetchall()
    customer_of = {r["alias"]: r["customer_id"] for r in requests}

    note = ""
    if sc["proxy_for"]:
        note = f"\n     * <p>⚠️ 代理編碼:{sc['proxy_for']}"
    lines = [
        "",
        f"    /** {sid} —— 來源:{sc['provenance']} {sc['provenance_ref']}"
        f"{note} */",
        "    @Test",
        f'    @DisplayName("{sid}: Given {_java_string(sc["given_when"])} '
        f'Then {_java_string(sc["then_expect"])}")',
        f"    void scenario_{sid}() {{",
    ]
    for req in requests:
        items = conn.execute(
            "SELECT * FROM rejected_request_item WHERE scenario_id = ? AND alias = ? "
            "ORDER BY seq", (sid, req["alias"]),
        ).fetchall()
        res = _var("res", req["alias"])
        lines.append(f'        ResponseEntity<String> {res} = placeOrder("""')
        lines.append(
            _request_body(wire, req["customer_id"], items,
                          req["claimed_total_cents"]) + '""");'
        )
    lines.append("")
    for assertion in assertions:
        lines.extend(
            _rejected_assertion_lines(assertion, customer_of[assertion["target_alias"]])
        )
    lines.append("    }")
    return "\n".join(lines) + "\n"


def _success_scenario(conn: sqlite3.Connection, wire: sqlite3.Row,
                      sc: sqlite3.Row) -> str:
    """預期成功的情境。"""
    sid = sc["id"]
    steps = conn.execute(
        "SELECT * FROM scenario_step WHERE scenario_id = ? ORDER BY seq", (sid,)
    ).fetchall()
    assertions = conn.execute(
        "SELECT * FROM scenario_assertion WHERE scenario_id = ? ORDER BY seq", (sid,)
    ).fetchall()

    needs_row = {a["target_alias"] for a in assertions if a["kind"].startswith("list_")}
    needs_id = needs_row | {
        a["target_alias"] for a in assertions if a["kind"] == "order_id_not_blank"
    }

    lines = [
        "",
        f"    /** {sid} —— 來源:{sc['provenance']} {sc['provenance_ref']}"
        + (f"\n     * <p>⚠️ 代理編碼(綠了不等於原文成立):{sc['proxy_for']}"
           if sc["proxy_for"] else "")
        + " */",
        "    @Test",
        f'    @DisplayName("{sid}: Given {_java_string(sc["given_when"])} '
        f'Then {_java_string(sc["then_expect"])}")',
        f"    void scenario_{sid}() {{",
    ]
    for step in steps:
        items = conn.execute(
            "SELECT * FROM step_item WHERE scenario_id = ? AND alias = ? ORDER BY seq",
            (sid, step["alias"]),
        ).fetchall()
        res = _var("res", step["alias"])
        lines.append(f'        ResponseEntity<String> {res} = placeOrder("""')
        lines.append(
            _request_body(wire, step["customer_id"], items,
                          step["claimed_total_cents"]) + '""");'
        )
        if step["alias"] in needs_id:
            lines.append(f'        String {_var("id", step["alias"])} = orderIdOf({res});')
    for alias in sorted(needs_row):
        lines.append(
            f'        Map<String, Object> {_var("row", alias)} = '
            f'findInList({_var("id", alias)});'
        )
    lines.append("")
    for assertion in assertions:
        lines.extend(_assertion_lines(assertion))
    lines.append("    }")
    return "\n".join(lines) + "\n"


def _render(conn: sqlite3.Connection, wire: sqlite3.Row, class_name: str,
            javadoc: str, scenarios: list[sqlite3.Row]) -> str:
    body = HEADER.replace("__CLASS_NAME__", class_name).replace("__JAVADOC__", javadoc)
    for sc in scenarios:
        body += (_rejection_scenario(conn, wire, sc) if sc["expects_rejection"]
                 else _success_scenario(conn, wire, sc)) + "\n"
    helper = ""
    if wire["res_customer_id_field"]:
        helper = CUSTOMER_IDS_HELPER.replace(
            "__CUSTOMER_ID_FIELD__", wire["res_customer_id_field"])
    return body + (FOOTER
                   .replace("__CONTRACT_NAME__", wire["name"])
                   .replace("__ORDER_ID_FIELD__", wire["res_order_id_field"])
                   .replace("__CUSTOMER_IDS_HELPER__", helper))


def generate(db_path: str | Path, out_path: str | Path) -> list[str]:
    """生兩個 class(2026-08-18,Nat 拍板):

      * `OrderAcceptanceTest`      —— 真情境。**這個 class 全綠才叫驗收通過。**
      * `OrderProxyAcceptanceTest` —— 代理編碼的情境,寫到 out_path 的**兄弟檔**。

    為什麼分開:代理編碼的情境**綠了不代表原文成立**(它的 fixture 不包含
    given_when 描述的那個動作)。混在同一個 class 就等於混在同一份綠燈裡,
    而一份混了 4 條「不可能因為它宣稱的理由而失敗」的綠燈,講不出任何事。

    2026-08-18 的第二幕重跑量到:12 條落檔裡有 4 條是代理編碼,而落檔率
    (12/12)完全看不出真實覆蓋只有 8。分 class 是為了讓那個差距在**跑測試**
    的時候就看得見,不用回去查 store。
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        scenarios = conn.execute(
            "SELECT * FROM acceptance_scenario ORDER BY length(id), id"
        ).fetchall()
        if not scenarios:
            # ⚠️ 不是 `SystemExit` —— 見 `NothingToGenerate` 的 docstring。
            raise NothingToGenerate("store 裡沒有驗收情境,沒有東西可生成")

        wire = conn.execute("SELECT * FROM wire_contract WHERE id = 1").fetchone()
        if wire is None:
            # 生成器不再自己填欄位名(ADR 0004)。沒宣告就不生 ——
            # 猜出來的名字跟實作全對不上,全紅,而紅的原因看不出是命名。
            #
            # ⚠️ 這一條跟上面那條**不是同一件事**,訊息要分得開:上面是「這份 store
            #    沒有驗收這一塊」,這裡是「有情境卻沒宣告 wire shape」—— 規格缺了
            #    一塊,而不是它本來就不談驗收。兩者都用 `NothingToGenerate`
            #    (呼叫方都比不了),但**理由要照原文印出去**,不准糊成一句。
            raise NothingToGenerate(
                f"store 裡有 {len(scenarios)} 條驗收情境,卻沒有 wire_contract —— "
                "wire shape 歸規格擁有(ADR 0004),沒宣告就不生。"
                "**這是規格缺了一塊,不是這份 store 不談驗收。**"
            )

        real = [sc for sc in scenarios if not sc["proxy_for"]]
        proxy = [sc for sc in scenarios if sc["proxy_for"]]

        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(_render(conn, wire, CLASS_NAME, MAIN_JAVADOC, real), encoding="utf-8")
        generated = [f"{CLASS_NAME}.scenario_{sc['id']}" for sc in real]

        proxy_path = out.parent / f"{PROXY_CLASS_NAME}.java"
        if proxy:
            proxy_path.write_text(
                _render(conn, wire, PROXY_CLASS_NAME, PROXY_JAVADOC, proxy), encoding="utf-8"
            )
            generated += [f"{PROXY_CLASS_NAME}.scenario_{sc['id']}" for sc in proxy]
        elif proxy_path.exists():
            # 沒有代理編碼了就把檔案刪掉 —— 留著會讓 drift check 拿舊的比新的。
            proxy_path.unlink()
        return generated
    finally:
        conn.close()


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        names = generate(argv[1], argv[2])
    except NothingToGenerate as exc:
        # 3 = 不適用,跟「用法錯誤」(2)分得開。原本這裡是 `SystemExit` 的 1。
        print(f"不適用(不是通過):{exc}", file=sys.stderr)
        return 3
    for name in names:
        print(f"  {name}")
    print(f"ok: {argv[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
