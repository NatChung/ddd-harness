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

    /** S1 —— 來源:Qn [Q1][Q2][Q8][Q12] — SPEC.md L41-L46(情境 S1);幣別 C7 見 L184 */
    @Test
    @DisplayName("S1: Given 客人 C-001 已登入,購物內容為「藍色馬克杯」1 個、單價 TWD 150.00; 他按下「確定」送出訂單 Then 系統建立一筆訂單,狀態「已成立」;含 1 項明細(藍色馬克杯 × 1、單價 TWD 150.00); 總金額 TWD 150.00;幣別 TWD;成立日期為送出當下;下單客人為 C-001")
    void scenario_S1() {
        ResponseEntity<String> resS1Order = placeOrder("""
                {"customerId":"C-001","items":[
                  {"productId":"P-MUG-BLUE","quantity":1,"unitPriceCents":15000,"currency":"TWD"}
                ]}""");
        String idS1Order = orderIdOf(resS1Order);
        Map<String, Object> rowS1Order = findInList(idS1Order);

        assertThat(resS1Order.getStatusCode().value())
                .isEqualTo(201);
        assertThat(idS1Order).isNotBlank();
        assertThat(rowS1Order).as("列表中找不到訂單 %s", idS1Order).isNotNull();
        assertThat(rowS1Order.get("customerId"))
                .isEqualTo("C-001");
        assertThat(((Number) rowS1Order.get("totalCents")).longValue())
                .isEqualTo(15000L);
        assertThat(rowS1Order.get("currency"))
                .isEqualTo("TWD");
        assertThat(rowS1Order.get("status"))
                .isEqualTo("已成立");
        assertThat(rowS1Order.get("placedAt")).isNotNull();
        assertThat(LocalDate.parse(rowS1Order.get("placedAt").toString()))
                .isNotNull();
    }


    /** S2 —— 來源:Qn [Q8] — SPEC.md L48-L53(情境 S2);不變式 C1 見 L178 */
    @Test
    @DisplayName("S2: Given 客人 C-002 已登入,購物內容為「藍色馬克杯」2 個(單價 TWD 150.00) 與「棉質提袋」3 個(單價 TWD 89.50);他按下「確定」送出訂單 Then 訂單成立,狀態「已成立」;總金額為 TWD 568.50(150.00 × 2 + 89.50 × 3), 且該數字由系統計算,不接受任何外部指定值")
    void scenario_S2() {
        ResponseEntity<String> resS2Order = placeOrder("""
                {"customerId":"C-002","items":[
                  {"productId":"P-MUG-BLUE","quantity":2,"unitPriceCents":15000,"currency":"TWD"},
                  {"productId":"P-TOTE-COTTON","quantity":3,"unitPriceCents":8950,"currency":"TWD"}
                ]}""");
        String idS2Order = orderIdOf(resS2Order);
        Map<String, Object> rowS2Order = findInList(idS2Order);

        assertThat(resS2Order.getStatusCode().value())
                .isEqualTo(201);
        assertThat(idS2Order).isNotBlank();
        assertThat(rowS2Order).as("列表中找不到訂單 %s", idS2Order).isNotNull();
        assertThat(rowS2Order.get("customerId"))
                .isEqualTo("C-002");
        assertThat(((Number) rowS2Order.get("totalCents")).longValue())
                .isEqualTo(56850L);
        assertThat(rowS2Order.get("status"))
                .isEqualTo("已成立");
    }


    /** S3 —— 來源:Qn [Q8] — SPEC.md L55-L60(情境 S3);不變式 C1 見 L178 */
    @Test
    @DisplayName("S3: Given 客人 C-003 已登入,購物內容為「棉質提袋」1 個、單價 TWD 89.50; 送出訂單時請求中夾帶一個總金額 TWD 50.00 Then 該指定值一律被忽略;訂單仍成立,成立的訂單總金額為 TWD 89.50")
    void scenario_S3() {
        ResponseEntity<String> resS3Order = placeOrder("""
                {"customerId":"C-003","totalCents":5000,"items":[
                  {"productId":"P-TOTE-COTTON","quantity":1,"unitPriceCents":8950,"currency":"TWD"}
                ]}""");
        String idS3Order = orderIdOf(resS3Order);
        Map<String, Object> rowS3Order = findInList(idS3Order);

        assertThat(resS3Order.getStatusCode().value())
                .isEqualTo(201);
        assertThat(idS3Order).isNotBlank();
        assertThat(rowS3Order).as("列表中找不到訂單 %s", idS3Order).isNotNull();
        assertThat(((Number) rowS3Order.get("totalCents")).longValue())
                .isEqualTo(8950L);
        assertThat(rowS3Order.get("status"))
                .isEqualTo("已成立");
    }


    /** S4 —— 來源:Qn [Q11] — SPEC.md L62-L67(情境 S4);不留紀錄為 推導自 [Q11],見 L67 與 C10 L187 */
    @Test
    @DisplayName("S4: Given 客人 C-004 已登入,購物內容為空、一項商品都沒有;他按下「確定」送出訂單 Then 系統拒絕(400);不產生任何訂單紀錄,資料庫中不留下任何殘骸")
    void scenario_S4() {
        ResponseEntity<String> resS4Request = placeOrder("""
                {"customerId":"C-004","items":[]}""");

        assertThat(resS4Request.getStatusCode().value())
                .as("請求應被拒絕,body=%s", resS4Request.getBody())
                .isEqualTo(400);
        assertThat(customerIdsInList())
                .as("請求被拒了,列表卻出現屬於這個客人的訂單")
                .doesNotContain("C-004");
    }


    /** S5 —— 來源:Qn [Q11] — SPEC.md L69-L74(情境 S5);C6 L183、C10 L187 */
    @Test
    @DisplayName("S5: Given 客人 C-005 已登入,購物內容為「藍色馬克杯」0 個、單價 TWD 150.00; 他按下「確定」送出訂單 Then 系統拒絕(400);不產生任何訂單紀錄")
    void scenario_S5() {
        ResponseEntity<String> resS5Request = placeOrder("""
                {"customerId":"C-005","items":[
                  {"productId":"P-MUG-BLUE","quantity":0,"unitPriceCents":15000,"currency":"TWD"}
                ]}""");

        assertThat(resS5Request.getStatusCode().value())
                .as("請求應被拒絕,body=%s", resS5Request.getBody())
                .isEqualTo(400);
        assertThat(customerIdsInList())
                .as("請求被拒了,列表卻出現屬於這個客人的訂單")
                .doesNotContain("C-005");
    }


    /** S6 —— 來源:Qn [Q11] — SPEC.md L76-L81(情境 S6);C6 L183、C10 L187 */
    @Test
    @DisplayName("S6: Given 客人 C-006 已登入,購物內容為「藍色馬克杯」-1 個、單價 TWD 150.00; 他按下「確定」送出訂單 Then 系統拒絕(400);不產生任何訂單紀錄")
    void scenario_S6() {
        ResponseEntity<String> resS6Request = placeOrder("""
                {"customerId":"C-006","items":[
                  {"productId":"P-MUG-BLUE","quantity":-1,"unitPriceCents":15000,"currency":"TWD"}
                ]}""");

        assertThat(resS6Request.getStatusCode().value())
                .as("請求應被拒絕,body=%s", resS6Request.getBody())
                .isEqualTo(400);
        assertThat(customerIdsInList())
                .as("請求被拒了,列表卻出現屬於這個客人的訂單")
                .doesNotContain("C-006");
    }


    /** S7 —— 來源:Qn [Q12] — SPEC.md L83-L88(情境 S7);C8 L185(跨聚合根,邊界可能錯,見 L190) */
    @Test
    @DisplayName("S7: Given 一名未登入的訪客,購物內容為「藍色馬克杯」1 個、單價 TWD 150.00;他送出訂單 Then 系統拒絕(401);不產生任何訂單紀錄")
    void scenario_S7() {
        ResponseEntity<String> resS7Request = placeOrder("""
                {"customerId":"","items":[
                  {"productId":"P-MUG-BLUE","quantity":1,"unitPriceCents":15000,"currency":"TWD"}
                ]}""");

        assertThat(resS7Request.getStatusCode().value())
                .as("請求應被拒絕,body=%s", resS7Request.getBody())
                .isEqualTo(401);
        assertThat(customerIdsInList())
                .as("請求被拒了,列表卻出現屬於這個客人的訂單")
                .doesNotContain("");
    }


    /** S11 —— 來源:Qn [Q2][Q14] — SPEC.md L112-L117(情境 S11);列表欄位見 L21 */
    @Test
    @DisplayName("S11: Given 系統中存在 3 筆已成立訂單,分屬客人 C-001、C-002、C-007;營運人員開啟訂單列表 Then 3 筆全部列出,每筆顯示:下單客人、商品項目、各項數量、各項單價、幣別、 成立日期、狀態、總金額;不提供搜尋框、篩選器或排序控制")
    void scenario_S11() {
        ResponseEntity<String> resS11OrderA = placeOrder("""
                {"customerId":"C-001","items":[
                  {"productId":"P-MUG-BLUE","quantity":1,"unitPriceCents":15000,"currency":"TWD"}
                ]}""");
        String idS11OrderA = orderIdOf(resS11OrderA);
        ResponseEntity<String> resS11OrderB = placeOrder("""
                {"customerId":"C-002","items":[
                  {"productId":"P-MUG-BLUE","quantity":2,"unitPriceCents":15000,"currency":"TWD"},
                  {"productId":"P-TOTE-COTTON","quantity":3,"unitPriceCents":8950,"currency":"TWD"}
                ]}""");
        String idS11OrderB = orderIdOf(resS11OrderB);
        ResponseEntity<String> resS11OrderC = placeOrder("""
                {"customerId":"C-007","items":[
                  {"productId":"P-TOTE-COTTON","quantity":1,"unitPriceCents":8950,"currency":"TWD"}
                ]}""");
        String idS11OrderC = orderIdOf(resS11OrderC);
        Map<String, Object> rowS11OrderA = findInList(idS11OrderA);
        Map<String, Object> rowS11OrderB = findInList(idS11OrderB);
        Map<String, Object> rowS11OrderC = findInList(idS11OrderC);

        assertThat(rowS11OrderA).as("列表中找不到訂單 %s", idS11OrderA).isNotNull();
        assertThat(rowS11OrderA.get("customerId"))
                .isEqualTo("C-001");
        assertThat(((Number) rowS11OrderA.get("totalCents")).longValue())
                .isEqualTo(15000L);
        assertThat(rowS11OrderA.get("placedAt")).isNotNull();
        assertThat(LocalDate.parse(rowS11OrderA.get("placedAt").toString()))
                .isNotNull();
        assertThat(rowS11OrderB).as("列表中找不到訂單 %s", idS11OrderB).isNotNull();
        assertThat(rowS11OrderB.get("customerId"))
                .isEqualTo("C-002");
        assertThat(((Number) rowS11OrderB.get("totalCents")).longValue())
                .isEqualTo(56850L);
        assertThat(rowS11OrderC).as("列表中找不到訂單 %s", idS11OrderC).isNotNull();
        assertThat(rowS11OrderC.get("customerId"))
                .isEqualTo("C-007");
        assertThat(((Number) rowS11OrderC.get("totalCents")).longValue())
                .isEqualTo(8950L);
        assertThat(rowS11OrderC.get("status"))
                .isEqualTo("已成立");
    }


    // ---------- helpers ----------
    //
    // 欄位名來自 spec 宣告的 wire 合約「shop-orders-v1」(ADR 0004),
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
                .map(r -> String.valueOf(r.get("customerId")))
                .toList();
    }
}
