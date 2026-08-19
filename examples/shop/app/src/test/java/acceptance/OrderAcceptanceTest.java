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
 * 驗收套件 —— 由 harness 提供。**實作者不得修改本檔案。**
 *
 * 這裡刻意「不 import 任何實作類別」——唯一引用的 com.shop 類別是 harness
 * 自己的 Application(啟動用)。整份驗收只透過 HTTP 進行,所以它不綁任何
 * 實作的類別名稱、不綁任何內部結構 —— 兩份長得完全不同的實作,
 * 都能被這同一套驗收明確判定。骨架(還沒有任何實作)時它必須是紅的。
 */
@SpringBootTest(
        classes = com.shop.Application.class,
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@DisplayName("驗收:下單(Command)與訂單列表(Query)")
class OrderAcceptanceTest {

    @Autowired
    private TestRestTemplate rest;

    private final ObjectMapper mapper = new ObjectMapper();

    // ---------- Scenario 1 ----------
    @Test
    @DisplayName("Given 一位存在的顧客 When 送出一筆含單一明細的訂單 Then 回 201 並帶回 orderId")
    void 下單成功回傳訂單編號() {
        ResponseEntity<String> res = placeOrder("""
                {"customerId":"C-001","items":[
                  {"productId":"P-100","quantity":2,"unitPriceCents":1500,"currency":"TWD"}
                ]}""");

        assertThat(res.getStatusCode().value()).isEqualTo(201);
        assertThat(orderIdOf(res)).isNotBlank();
    }

    // ---------- Scenario 2 ----------
    @Test
    @DisplayName("Given 一筆已成立的訂單 When 查詢訂單列表 Then 該筆出現在列表中,狀態為「已成立」")
    void 列表看得到剛成立的訂單() {
        String orderId = orderIdOf(placeOrder("""
                {"customerId":"C-001","items":[
                  {"productId":"P-100","quantity":1,"unitPriceCents":1000,"currency":"TWD"}
                ]}"""));

        Map<String, Object> row = findInList(orderId);

        assertThat(row).as("列表中找不到剛成立的訂單 %s", orderId).isNotNull();
        assertThat(row.get("statusLabel")).isEqualTo("已成立");
    }

    // ---------- Scenario 3 ----------
    @Test
    @DisplayName("Given 訂單只持有 CustomerId When 查詢訂單列表 Then 列表仍顯示顧客姓名")
    void 列表顯示顧客姓名() {
        String alice = orderIdOf(placeOrder("""
                {"customerId":"C-001","items":[
                  {"productId":"P-100","quantity":1,"unitPriceCents":1000,"currency":"TWD"}
                ]}"""));
        String bob = orderIdOf(placeOrder("""
                {"customerId":"C-002","items":[
                  {"productId":"P-200","quantity":1,"unitPriceCents":2000,"currency":"TWD"}
                ]}"""));

        assertThat(findInList(alice)).isNotNull();
        assertThat(findInList(alice).get("customerName")).isEqualTo("Alice");
        assertThat(findInList(bob).get("customerName")).isEqualTo("Bob");
    }

    // ---------- Scenario 4 ----------
    @Test
    @DisplayName("Given 一筆含多個明細的訂單 When 查詢訂單列表 Then totalCents 等於各明細金額加總")
    void 總金額為各明細加總() {
        String orderId = orderIdOf(placeOrder("""
                {"customerId":"C-001","items":[
                  {"productId":"P-100","quantity":2,"unitPriceCents":1500,"currency":"TWD"},
                  {"productId":"P-200","quantity":3,"unitPriceCents":700,"currency":"TWD"}
                ]}"""));

        Map<String, Object> row = findInList(orderId);

        assertThat(row).isNotNull();
        // 2 * 1500 + 3 * 700 = 5100
        assertThat(((Number) row.get("totalCents")).longValue()).isEqualTo(5100L);
    }

    // ---------- Scenario 5 ----------
    @Test
    @DisplayName("Given 一筆已成立的訂單 When 查詢訂單列表 Then placedAt 是一個 ISO 日期")
    void 列表帶出成立日期() {
        String orderId = orderIdOf(placeOrder("""
                {"customerId":"C-002","items":[
                  {"productId":"P-300","quantity":1,"unitPriceCents":500,"currency":"TWD"}
                ]}"""));

        Map<String, Object> row = findInList(orderId);

        assertThat(row).isNotNull();
        assertThat(row.get("placedAt")).isNotNull();
        assertThat(LocalDate.parse(row.get("placedAt").toString())).isNotNull();
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
            List<Map<String, Object>> rows = mapper.readValue(res.getBody(), new TypeReference<>() {});
            return rows.stream()
                    .filter(r -> orderId.equals(String.valueOf(r.get("orderId"))))
                    .findFirst()
                    .orElse(null);
        } catch (Exception e) {
            throw new AssertionError("GET /orders 的回應不是預期的 JSON 陣列:" + res.getBody(), e);
        }
    }
}
