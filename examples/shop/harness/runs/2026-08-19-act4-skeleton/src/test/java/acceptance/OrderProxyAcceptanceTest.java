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
 * 生成物 —— <b>代理編碼的情境</b>,由 tools/harness/gen_acceptance.py 產生。
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
 */
@SpringBootTest(
        classes = com.shop.Application.class,
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@DisplayName("驗收(生成物):下單(Command)與訂單列表(Query)")
class OrderProxyAcceptanceTest {

    @Autowired
    private TestRestTemplate rest;

    private final ObjectMapper mapper = new ObjectMapper();

    /** G1 —— 來源:Qn SPEC.md L213-L216(來源 [Q3] [Q8],逐字見 L521、L526)
     * <p>⚠️ 代理編碼(綠了不等於原文成立):散文的 G1 有運費 120、Then 的 totalAmount 是 6520。本檔的 fixture 詞彙**沒有運費** —— 一個品項只有 product_id / quantity / unit_price_cents / currency,而列表的總金額欄 是靠「總額 = Σ(數量 × 單價)」認人的。故此處以**不含運費的請求**代替原情境, 斷言的 totalAmount 是商品金額合計 6400。後果:C2 公式「Σ(單價 × 數量) + 運費」 只有前半被驗到,**「+ 運費」那一半本檔驗不到**;庫存 5 雙、結帳作業、付款回報 這三個 Given/When 也不在 fixture 裡,本情境驗的是「一次下單請求成立並落進列表」。 */
    @Test
    @DisplayName("G1: Given SKU NIKE-DUNK-LOW-US9 庫存 5 雙、單價 3200、運費 120;客戶以數量 2 建立結帳作業取得 checkoutId,第三方支付回報 pay_0001 付費成功,以該 checkoutId + paymentId 建立訂單。 Then 回 201;orderId 不為空;該訂單出現在 GET /orders 的列表裡;status = PLACED; itemCount = 2;placedAt 是 ISO-8601 日期時間;totalAmount = 2 × 3200 = 6400 (商品金額合計;運費那一項見 proxy_for)。")
    void scenario_G1() {
        ResponseEntity<String> resOrder1 = placeOrder("""
                {"customer":"王小明","items":[
                  {"sku":"NIKE-DUNK-LOW-US9","quantity":2,"unitPrice":3200,"currency":"TWD"}
                ]}""");
        String idOrder1 = orderIdOf(resOrder1);
        Map<String, Object> rowOrder1 = findInList(idOrder1);

        assertThat(resOrder1.getStatusCode().value())
                .isEqualTo(201);
        assertThat(idOrder1).isNotBlank();
        assertThat(rowOrder1).as("列表中找不到訂單 %s", idOrder1).isNotNull();
        assertThat(rowOrder1.get("customerName"))
                .isEqualTo("王小明");
        assertThat(rowOrder1.get("status"))
                .isEqualTo("PLACED");
        assertThat(rowOrder1.get("currency"))
                .isEqualTo("TWD");
        assertThat(((Number) rowOrder1.get("totalAmount")).longValue())
                .isEqualTo(6400L);
        assertThat(((Number) rowOrder1.get("itemCount")).longValue())
                .isEqualTo(2L);
        assertThat(rowOrder1.get("placedAt")).isNotNull();
        assertThat(LocalDate.parse(rowOrder1.get("placedAt").toString()))
                .isNotNull();
    }


    /** G2 —— 來源:Qn SPEC.md L218-L221(來源 [Q16] [Q21] [Q26],逐字見 L534、L539、L544)
     * <p>⚠️ 代理編碼(綠了不等於原文成立):同 G1:散文的 totalAmount 是 6400 + 4500 + 120 = 11020,而 fixture 沒有運費欄位, 故以不含運費的請求代替,斷言 10900。C2 的「+ 運費」那一半本檔驗不到。 lineSubtotal(品項小計)也不在列表一列的欄位裡(E3,L155-L171), 故散文 Then 的「lineSubtotal 分別為 6400 與 4500」本檔只能靠總額間接驗到。 */
    @Test
    @DisplayName("G2: Given SKU A 單價 3200 庫存 5、SKU B 單價 4500 庫存 2、運費 120;同一次結帳 A 買 2 雙、 B 買 1 雙,付費成功後產生訂單。 Then 回 201;orderId 不為空;該訂單在列表裡;itemCount = 3; totalAmount = 6400 + 4500 = 10900(商品金額合計;運費那一項見 proxy_for)。")
    void scenario_G2() {
        ResponseEntity<String> resOrder1 = placeOrder("""
                {"customer":"王小明","items":[
                  {"sku":"NIKE-DUNK-LOW-US9","quantity":2,"unitPrice":3200,"currency":"TWD"},
                  {"sku":"NIKE-AIR-FORCE1-US9","quantity":1,"unitPrice":4500,"currency":"TWD"}
                ]}""");
        String idOrder1 = orderIdOf(resOrder1);
        Map<String, Object> rowOrder1 = findInList(idOrder1);

        assertThat(resOrder1.getStatusCode().value())
                .isEqualTo(201);
        assertThat(idOrder1).isNotBlank();
        assertThat(rowOrder1).as("列表中找不到訂單 %s", idOrder1).isNotNull();
        assertThat(((Number) rowOrder1.get("totalAmount")).longValue())
                .isEqualTo(10900L);
        assertThat(((Number) rowOrder1.get("itemCount")).longValue())
                .isEqualTo(3L);
        assertThat(rowOrder1.get("status"))
                .isEqualTo("PLACED");
    }


    /** G13 —— 來源:Qn SPEC.md L273-L274(來源:需求方第一句原話「我能看到所有訂單」+ [Q25],逐字見 L543)
     * <p>⚠️ 代理編碼(綠了不等於原文成立):散文的 When 是「**後台人員**呼叫 GET /orders」。本檔沒有身分:B-2(身分驗證)是阻斷級 規格沉默(L350),§10 明寫 GET /orders 本次一律回所有訂單、不得實作任何身分模型 (L509)。故此處以「不帶身分呼叫列表」代替「後台人員呼叫」,驗的是 「三張都在同一份列表裡」,**驗不到「後台人員」與「用戶」的可見範圍差異**(那是 G15, 依 B-2 阻斷、不入驗收套件)。 */
    @Test
    @DisplayName("G13: Given 三張分屬不同客戶的訂單;後台人員呼叫 GET /orders。 Then 三張都在列表裡,每一列的 customerName 各自對得回它自己的下單者, 欄位如 §1.2 E3(L155-L171)。")
    void scenario_G13() {
        ResponseEntity<String> resOrder1 = placeOrder("""
                {"customer":"王小明","items":[
                  {"sku":"NIKE-DUNK-LOW-US9","quantity":1,"unitPrice":3200,"currency":"TWD"}
                ]}""");
        String idOrder1 = orderIdOf(resOrder1);
        ResponseEntity<String> resOrder2 = placeOrder("""
                {"customer":"李美華","items":[
                  {"sku":"NIKE-AIR-FORCE1-US9","quantity":2,"unitPrice":4500,"currency":"TWD"}
                ]}""");
        String idOrder2 = orderIdOf(resOrder2);
        ResponseEntity<String> resOrder3 = placeOrder("""
                {"customer":"張志豪","items":[
                  {"sku":"NIKE-DUNK-LOW-US9","quantity":1,"unitPrice":3200,"currency":"TWD"}
                ]}""");
        String idOrder3 = orderIdOf(resOrder3);
        Map<String, Object> rowOrder1 = findInList(idOrder1);
        Map<String, Object> rowOrder2 = findInList(idOrder2);
        Map<String, Object> rowOrder3 = findInList(idOrder3);

        assertThat(resOrder1.getStatusCode().value())
                .isEqualTo(201);
        assertThat(resOrder2.getStatusCode().value())
                .isEqualTo(201);
        assertThat(resOrder3.getStatusCode().value())
                .isEqualTo(201);
        assertThat(rowOrder1).as("列表中找不到訂單 %s", idOrder1).isNotNull();
        assertThat(rowOrder2).as("列表中找不到訂單 %s", idOrder2).isNotNull();
        assertThat(rowOrder3).as("列表中找不到訂單 %s", idOrder3).isNotNull();
        assertThat(rowOrder1.get("customerName"))
                .isEqualTo("王小明");
        assertThat(rowOrder2.get("customerName"))
                .isEqualTo("李美華");
        assertThat(rowOrder3.get("customerName"))
                .isEqualTo("張志豪");
        assertThat(((Number) rowOrder2.get("totalAmount")).longValue())
                .isEqualTo(9000L);
        assertThat(((Number) rowOrder2.get("itemCount")).longValue())
                .isEqualTo(2L);
        assertThat(rowOrder3.get("placedAt")).isNotNull();
        assertThat(LocalDate.parse(rowOrder3.get("placedAt").toString()))
                .isNotNull();
    }


    /** G17 —— 來源:本案自決 SPEC.md L287;依據 §6 A-1「金額…不可為負」(L370)、§3 C4(L298)
     * <p>⚠️ 代理編碼:散文的 G17 是「`unitPrice` **或** `shippingFee` 為負 → 回 400」。fixture 沒有運費欄位 (見 G1 的 proxy_for),故本情境只送得出負的 unitPrice,**shippingFee 為負那一半驗不到**。 */
    @Test
    @DisplayName("G17: Given 下單請求裡的 unitPrice 是負數(-3200)。 Then 回 400;訂單列表裡沒有任何一列屬於這個下單者。")
    void scenario_G17() {
        ResponseEntity<String> resNegativePrice = placeOrder("""
                {"customer":"cust-rej-price-negative","items":[
                  {"sku":"NIKE-DUNK-LOW-US9","quantity":1,"unitPrice":-3200,"currency":"TWD"}
                ]}""");

        assertThat(resNegativePrice.getStatusCode().value())
                .as("請求應被拒絕,body=%s", resNegativePrice.getBody())
                .isEqualTo(400);
        assertThat(customerIdsInList())
                .as("請求被拒了,列表卻出現屬於這個客人的訂單")
                .doesNotContain("cust-rej-price-negative");
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
