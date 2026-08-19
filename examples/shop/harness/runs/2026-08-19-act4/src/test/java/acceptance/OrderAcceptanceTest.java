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

    /** G16 —— 來源:本案自決 SPEC.md L286;依據 §6 A-6「數量為 ≥ 1 的整數」(L375)、§3 C5(L299) */
    @Test
    @DisplayName("G16: Given 下單請求裡的數量是 0,或是負數(-1)。 Then 兩筆都回 400;訂單列表裡沒有任何一列屬於這兩個下單者 (散文的「不建立結帳作業」本檔驗不到 —— 結帳作業沒有查詢端點)。")
    void scenario_G16() {
        ResponseEntity<String> resZeroQuantity = placeOrder("""
                {"customer":"cust-rej-qty-zero","items":[
                  {"sku":"NIKE-DUNK-LOW-US9","quantity":0,"unitPrice":3200,"currency":"TWD"}
                ]}""");
        ResponseEntity<String> resNegativeQuantity = placeOrder("""
                {"customer":"cust-rej-qty-negative","items":[
                  {"sku":"NIKE-DUNK-LOW-US9","quantity":-1,"unitPrice":3200,"currency":"TWD"}
                ]}""");

        assertThat(resZeroQuantity.getStatusCode().value())
                .as("請求應被拒絕,body=%s", resZeroQuantity.getBody())
                .isEqualTo(400);
        assertThat(customerIdsInList())
                .as("請求被拒了,列表卻出現屬於這個客人的訂單")
                .doesNotContain("cust-rej-qty-zero");
        assertThat(resNegativeQuantity.getStatusCode().value())
                .as("請求應被拒絕,body=%s", resNegativeQuantity.getBody())
                .isEqualTo(400);
        assertThat(customerIdsInList())
                .as("請求被拒了,列表卻出現屬於這個客人的訂單")
                .doesNotContain("cust-rej-qty-negative");
    }


    // ---------- helpers ----------
    //
    // 欄位名來自 spec 宣告的 wire 合約「球鞋線上訂購系統對外 JSON 合約(SPEC.md §1.2,L79-L205)」(ADR 0004),
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

    /** 列表上所有訂單的客人編號。負面情境用它斷言「沒有屬於這個客人的列」。 */
    private List<String> customerIdsInList() {
        return listRows().stream()
                .map(r -> String.valueOf(r.get("customerName")))
                .toList();
    }
}
