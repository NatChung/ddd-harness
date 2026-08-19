package acceptance;

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

/**
 * 生成物 —— 由 tools/harness/gen_acceptance.py 從 spec store 產生。
 *
 * <p><b>不要手改這個檔案。</b>要改情境就改 spec,重新生成;
 * {@code verifyGenerated} 會抓到手改。
 *
 * <p>這裡刻意<b>不 import 任何實作類別</b> —— 唯一引用的 com.shop 類別是
 * harness 自己的 Application(啟動用)。整份驗收只透過 HTTP 進行,所以它
 * 不綁任何實作的類別名稱、不綁任何內部結構。骨架(還沒有任何實作)時它必須是紅的。
 */
@SpringBootTest(
        classes = com.shop.Application.class,
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@DisplayName("驗收(生成物):下單(Command)與訂單列表(Query)")
class OrderAcceptanceTest {

    @Autowired
    private TestRestTemplate rest;

    private final ObjectMapper mapper = new ObjectMapper();

    /** S1 —— 來源:Qn [Q1][Q2][Q8][Q12] spec/SPEC.md L41-L46 */
    @Test
    @DisplayName("S1: Given 客人 C-001 已登入,購物內容為商品「藍色馬克杯」1 個、單價 TWD 150.00; 他按下「確定」送出訂單。 Then 訂單成立,狀態為「已成立」;訂單具備識別碼;訂單含 1 項明細 (藍色馬克杯 × 1、單價 TWD 150.00);幣別為 TWD;總金額為 TWD 150.00; 成立日期為送出當下的時間;下單客人編號為 C-001。")
    void scenario_S1() {
        ResponseEntity<String> resOrder1 = placeOrder("""
                {"customerId":"C-001","items":[
                  {"productId":"blue-mug","quantity":1,"unitPriceCents":15000,"currency":"TWD"}
                ]}""");
        String idOrder1 = orderIdOf(resOrder1);
        Map<String, Object> rowOrder1 = findInList(idOrder1);

        assertThat(resOrder1.getStatusCode().value())
                .isEqualTo(201);
        assertThat(idOrder1).isNotBlank();
        assertThat(rowOrder1).as("列表中找不到訂單 %s", idOrder1).isNotNull();
        assertThat(rowOrder1.get("customer_id"))
                .isEqualTo("C-001");
        assertThat(rowOrder1.get("status"))
                .isEqualTo("已成立");
        assertThat(rowOrder1.get("currency"))
                .isEqualTo("TWD");
        assertThat(((Number) rowOrder1.get("total_cents")).longValue())
                .isEqualTo(15000L);
        assertThat(rowOrder1.get("created_at")).isNotNull();
        assertThat(LocalDate.parse(rowOrder1.get("created_at").toString()))
                .isNotNull();
    }

    /** S2 —— 來源:Qn [Q8] spec/SPEC.md L48-L53 */
    @Test
    @DisplayName("S2: Given 客人 C-002 已登入,購物內容為商品「藍色馬克杯」2 個(單價 TWD 150.00) 與商品「棉質提袋」3 個(單價 TWD 89.50);他按下「確定」送出訂單。 Then 訂單成立,狀態為「已成立」;總金額為 TWD 568.50,由系統以 Σ(單價 × 數量) 算出,不接受任何外部指定值。")
    void scenario_S2() {
        ResponseEntity<String> resOrder2 = placeOrder("""
                {"customerId":"C-002","items":[
                  {"productId":"blue-mug","quantity":2,"unitPriceCents":15000,"currency":"TWD"},
                  {"productId":"cotton-tote","quantity":3,"unitPriceCents":8950,"currency":"TWD"}
                ]}""");
        String idOrder2 = orderIdOf(resOrder2);
        Map<String, Object> rowOrder2 = findInList(idOrder2);

        assertThat(resOrder2.getStatusCode().value())
                .isEqualTo(201);
        assertThat(rowOrder2).as("列表中找不到訂單 %s", idOrder2).isNotNull();
        assertThat(rowOrder2.get("status"))
                .isEqualTo("已成立");
        assertThat(((Number) rowOrder2.get("total_cents")).longValue())
                .isEqualTo(56850L);
    }

    /** S10 —— 來源:Qn [Q9] spec/SPEC.md L105-L110 */
    @Test
    @DisplayName("S10: Given 客人 C-007 於商品「藍色馬克杯」單價為 TWD 100.00 時下單 1 個,訂單成立; 其後同一商品以單價 TWD 120.00 再成立一筆訂單(以此表達該商品的事後調價), 而後重新查看那筆舊訂單。 Then 舊訂單明細的單價仍為 TWD 100.00,總金額仍為 TWD 100.00; 新訂單的總金額為 TWD 120.00。兩筆訂單各自持有下單當時的單價複本。")
    void scenario_S10() {
        ResponseEntity<String> resOrderBeforeRepricing = placeOrder("""
                {"customerId":"C-007","items":[
                  {"productId":"blue-mug","quantity":1,"unitPriceCents":10000,"currency":"TWD"}
                ]}""");
        String idOrderBeforeRepricing = orderIdOf(resOrderBeforeRepricing);
        ResponseEntity<String> resOrderAfterRepricing = placeOrder("""
                {"customerId":"C-007","items":[
                  {"productId":"blue-mug","quantity":1,"unitPriceCents":12000,"currency":"TWD"}
                ]}""");
        String idOrderAfterRepricing = orderIdOf(resOrderAfterRepricing);
        Map<String, Object> rowOrderAfterRepricing = findInList(idOrderAfterRepricing);
        Map<String, Object> rowOrderBeforeRepricing = findInList(idOrderBeforeRepricing);

        assertThat(resOrderBeforeRepricing.getStatusCode().value())
                .isEqualTo(201);
        assertThat(resOrderAfterRepricing.getStatusCode().value())
                .isEqualTo(201);
        assertThat(rowOrderBeforeRepricing).as("列表中找不到訂單 %s", idOrderBeforeRepricing).isNotNull();
        assertThat(rowOrderAfterRepricing).as("列表中找不到訂單 %s", idOrderAfterRepricing).isNotNull();
        assertThat(((Number) rowOrderBeforeRepricing.get("total_cents")).longValue())
                .isEqualTo(10000L);
        assertThat(((Number) rowOrderAfterRepricing.get("total_cents")).longValue())
                .isEqualTo(12000L);
    }

    /** S11 —— 來源:Qn [Q2][Q14] spec/SPEC.md L112-L117 */
    @Test
    @DisplayName("S11: Given 系統中存在 3 筆已成立訂單,分屬客人 C-001、C-002、C-007; 營運人員開啟訂單列表,無任何查詢條件。 Then 3 筆全部列出,每筆顯示:下單客人編號、商品項目、各項數量、各項單價、幣別、 成立日期、狀態、總金額;不提供搜尋框、篩選器或排序控制。")
    void scenario_S11() {
        ResponseEntity<String> resListRow1 = placeOrder("""
                {"customerId":"C-001","items":[
                  {"productId":"blue-mug","quantity":1,"unitPriceCents":15000,"currency":"TWD"}
                ]}""");
        String idListRow1 = orderIdOf(resListRow1);
        ResponseEntity<String> resListRow2 = placeOrder("""
                {"customerId":"C-002","items":[
                  {"productId":"blue-mug","quantity":2,"unitPriceCents":15000,"currency":"TWD"},
                  {"productId":"cotton-tote","quantity":3,"unitPriceCents":8950,"currency":"TWD"}
                ]}""");
        String idListRow2 = orderIdOf(resListRow2);
        ResponseEntity<String> resListRow3 = placeOrder("""
                {"customerId":"C-007","items":[
                  {"productId":"blue-mug","quantity":1,"unitPriceCents":10000,"currency":"TWD"}
                ]}""");
        String idListRow3 = orderIdOf(resListRow3);
        Map<String, Object> rowListRow1 = findInList(idListRow1);
        Map<String, Object> rowListRow2 = findInList(idListRow2);
        Map<String, Object> rowListRow3 = findInList(idListRow3);

        assertThat(rowListRow1).as("列表中找不到訂單 %s", idListRow1).isNotNull();
        assertThat(rowListRow2).as("列表中找不到訂單 %s", idListRow2).isNotNull();
        assertThat(rowListRow3).as("列表中找不到訂單 %s", idListRow3).isNotNull();
        assertThat(rowListRow1.get("customer_id"))
                .isEqualTo("C-001");
        assertThat(rowListRow2.get("customer_id"))
                .isEqualTo("C-002");
        assertThat(rowListRow3.get("customer_id"))
                .isEqualTo("C-007");
        assertThat(((Number) rowListRow2.get("total_cents")).longValue())
                .isEqualTo(56850L);
        assertThat(rowListRow1.get("created_at")).isNotNull();
        assertThat(LocalDate.parse(rowListRow1.get("created_at").toString()))
                .isNotNull();
    }

    // ---------- helpers ----------

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
            Object id = body.get("orderId");
            assertThat(id).as("POST /orders 的回應缺少 orderId,body=%s", res.getBody()).isNotNull();
            return id.toString();
        } catch (Exception e) {
            throw new AssertionError("POST /orders 的回應不是預期的 JSON:" + res.getBody(), e);
        }
    }

    private Map<String, Object> findInList(String orderId) {
        ResponseEntity<String> res = rest.getForEntity("/orders", String.class);
        assertThat(res.getStatusCode().value())
                .as("GET /orders 應回 200,實際 %s,body=%s", res.getStatusCode(), res.getBody())
                .isEqualTo(200);
        try {
            List<Map<String, Object>> rows =
                    mapper.readValue(res.getBody(), new TypeReference<>() {});
            return rows.stream()
                    .filter(r -> orderId.equals(String.valueOf(r.get("orderId"))))
                    .findFirst()
                    .orElse(null);
        } catch (Exception e) {
            throw new AssertionError("GET /orders 的回應不是預期的 JSON:" + res.getBody(), e);
        }
    }
}
