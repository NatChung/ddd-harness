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
 *
 * <p><b>這個 class 全綠 = 驗收通過。</b>代理編碼的情境不在這裡,
 * 在 {@code OrderProxyAcceptanceTest} —— 那些綠了不算數。
 */
@SpringBootTest(
        classes = com.shop.Application.class,
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@DisplayName("驗收(生成物):下單(Command)與訂單列表(Query)")
class OrderAcceptanceTest {

    @Autowired
    private TestRestTemplate rest;

    private final ObjectMapper mapper = new ObjectMapper();

    /** S1 —— 來源:推導自 examples/shop/spec/SPEC.md L44-45 */
    @Test
    @DisplayName("S1: Given 一位存在的顧客送出一筆含單一明細的訂單 Then 回 201 並帶回 orderId")
    void scenario_S1() {
        ResponseEntity<String> resOrder = placeOrder("""
                {"customerId":"C-001","items":[
                  {"productId":"P-100","quantity":2,"unitPriceCents":1500,"currency":"TWD"}
                ]}""");
        String idOrder = orderIdOf(resOrder);

        assertThat(resOrder.getStatusCode().value())
                .isEqualTo(201);
        assertThat(idOrder).isNotBlank();
    }


    /** S2 —— 來源:推導自 examples/shop/spec/SPEC.md L46-47 */
    @Test
    @DisplayName("S2: Given 一筆已成立的訂單被查詢訂單列表 Then 該筆出現在列表中,statusLabel 為「已成立」")
    void scenario_S2() {
        ResponseEntity<String> resOrder = placeOrder("""
                {"customerId":"C-001","items":[
                  {"productId":"P-100","quantity":1,"unitPriceCents":1000,"currency":"TWD"}
                ]}""");
        String idOrder = orderIdOf(resOrder);
        Map<String, Object> rowOrder = findInList(idOrder);

        assertThat(rowOrder).as("列表中找不到訂單 %s", idOrder).isNotNull();
        assertThat(rowOrder.get("statusLabel"))
                .isEqualTo("已成立");
    }


    /** S3 —— 來源:推導自 examples/shop/spec/SPEC.md L48-49 */
    @Test
    @DisplayName("S3: Given 訂單只持有 CustomerId,查詢訂單列表 Then 列表仍顯示顧客姓名(來自 customers 表)")
    void scenario_S3() {
        ResponseEntity<String> resAlice = placeOrder("""
                {"customerId":"C-001","items":[
                  {"productId":"P-100","quantity":1,"unitPriceCents":1000,"currency":"TWD"}
                ]}""");
        String idAlice = orderIdOf(resAlice);
        ResponseEntity<String> resBob = placeOrder("""
                {"customerId":"C-002","items":[
                  {"productId":"P-200","quantity":1,"unitPriceCents":2000,"currency":"TWD"}
                ]}""");
        String idBob = orderIdOf(resBob);
        Map<String, Object> rowAlice = findInList(idAlice);
        Map<String, Object> rowBob = findInList(idBob);

        assertThat(rowAlice).as("列表中找不到訂單 %s", idAlice).isNotNull();
        assertThat(rowAlice.get("customerName"))
                .isEqualTo("Alice");
        assertThat(rowBob).as("列表中找不到訂單 %s", idBob).isNotNull();
        assertThat(rowBob.get("customerName"))
                .isEqualTo("Bob");
    }


    /** S4 —— 來源:推導自 examples/shop/spec/SPEC.md L50-51 */
    @Test
    @DisplayName("S4: Given 一筆含多個明細的訂單被查詢訂單列表 Then totalCents 等於各明細「數量 × 單價」的加總")
    void scenario_S4() {
        ResponseEntity<String> resOrder = placeOrder("""
                {"customerId":"C-001","items":[
                  {"productId":"P-100","quantity":2,"unitPriceCents":1500,"currency":"TWD"},
                  {"productId":"P-200","quantity":3,"unitPriceCents":700,"currency":"TWD"}
                ]}""");
        String idOrder = orderIdOf(resOrder);
        Map<String, Object> rowOrder = findInList(idOrder);

        assertThat(rowOrder).as("列表中找不到訂單 %s", idOrder).isNotNull();
        assertThat(((Number) rowOrder.get("totalCents")).longValue())
                .isEqualTo(5100L);
    }


    /** S5 —— 來源:推導自 examples/shop/spec/SPEC.md L52-53 */
    @Test
    @DisplayName("S5: Given 一筆已成立的訂單被查詢訂單列表 Then placedAt 是一個 ISO 日期(YYYY-MM-DD)")
    void scenario_S5() {
        ResponseEntity<String> resOrder = placeOrder("""
                {"customerId":"C-002","items":[
                  {"productId":"P-300","quantity":1,"unitPriceCents":500,"currency":"TWD"}
                ]}""");
        String idOrder = orderIdOf(resOrder);
        Map<String, Object> rowOrder = findInList(idOrder);

        assertThat(rowOrder).as("列表中找不到訂單 %s", idOrder).isNotNull();
        assertThat(rowOrder.get("placedAt")).isNotNull();
        assertThat(LocalDate.parse(rowOrder.get("placedAt").toString()))
                .isNotNull();
    }


    // ---------- helpers ----------
    //
    // 欄位名來自 spec 宣告的 wire 合約「shop-frozen-v1」(ADR 0004),
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
            Object id = body.get("orderId");
            assertThat(id).as("POST /orders 的回應缺少 orderId,body=%s", res.getBody()).isNotNull();
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
                .filter(r -> orderId.equals(String.valueOf(r.get("orderId"))))
                .findFirst()
                .orElse(null);
    }
}
