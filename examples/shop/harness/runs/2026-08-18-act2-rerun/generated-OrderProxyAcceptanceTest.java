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

    /** S8 —— 來源:Qn [Q7] — SPEC.md L91-L96(情境 S8);C3 L180
     * <p>⚠️ 代理編碼(綠了不等於原文成立):schema 沒有「修改已成立訂單」這個動作,且 expects_rejection 掛在情境上, 「成功的前置訂單 + 被拒的修改」表達不了(schema.sql L255-L257)。 代理:成立該筆訂單後,以列表仍顯示 數量 1 之總金額 15000、狀態「已成立」, 近似「修改被拒且內容不變」—— 只覆蓋到「內容不變」這一半, 「修改請求被拒」那一半本檔證明不了。 */
    @Test
    @DisplayName("S8: Given 已存在一筆已成立訂單,客人 C-001,含「藍色馬克杯」1 個(單價 TWD 150.00)、 總金額 TWD 150.00;有人(客人或營運人員)嘗試把數量改成 2 Then 系統拒絕;該訂單的明細、總金額、狀態、成立日期完全不變, 仍為「藍色馬克杯 × 1、TWD 150.00、已成立」")
    void scenario_S8() {
        ResponseEntity<String> resS8Order = placeOrder("""
                {"customerId":"C-001","items":[
                  {"productId":"P-MUG-BLUE","quantity":1,"unitPriceCents":15000,"currency":"TWD"}
                ]}""");
        String idS8Order = orderIdOf(resS8Order);
        Map<String, Object> rowS8Order = findInList(idS8Order);

        assertThat(resS8Order.getStatusCode().value())
                .isEqualTo(201);
        assertThat(rowS8Order).as("列表中找不到訂單 %s", idS8Order).isNotNull();
        assertThat(((Number) rowS8Order.get("totalCents")).longValue())
                .isEqualTo(15000L);
        assertThat(rowS8Order.get("status"))
                .isEqualTo("已成立");
        assertThat(rowS8Order.get("placedAt")).isNotNull();
        assertThat(LocalDate.parse(rowS8Order.get("placedAt").toString()))
                .isNotNull();
    }


    /** S9 —— 來源:Qn [Q7][Q6] — SPEC.md L98-L103(情境 S9);C2 L179、C3 L180
     * <p>⚠️ 代理編碼(綠了不等於原文成立):schema 沒有「取消訂單」這個動作。代理:成立一筆訂單後,以列表該列狀態仍為 「已成立」近似「取消被拒、狀態不變」—— 「不存在已取消狀態」只被 「唯一觀察得到的狀態值是已成立」間接覆蓋,取消請求本身本檔送不出去。 */
    @Test
    @DisplayName("S9: Given 同 S8 的那筆已成立訂單;有人嘗試取消它 Then 系統拒絕;訂單狀態仍為「已成立」;系統中不存在「已取消」這個狀態")
    void scenario_S9() {
        ResponseEntity<String> resS9Order = placeOrder("""
                {"customerId":"C-001","items":[
                  {"productId":"P-MUG-BLUE","quantity":1,"unitPriceCents":15000,"currency":"TWD"}
                ]}""");
        String idS9Order = orderIdOf(resS9Order);
        Map<String, Object> rowS9Order = findInList(idS9Order);

        assertThat(resS9Order.getStatusCode().value())
                .isEqualTo(201);
        assertThat(rowS9Order).as("列表中找不到訂單 %s", idS9Order).isNotNull();
        assertThat(rowS9Order.get("status"))
                .isEqualTo("已成立");
        assertThat(((Number) rowS9Order.get("totalCents")).longValue())
                .isEqualTo(15000L);
    }


    /** S10 —— 來源:Qn [Q9] — SPEC.md L105-L110(情境 S10,100/120 為親口確認);C4 L181
     * <p>⚠️ 代理編碼(綠了不等於原文成立):schema 沒有「調整商品單價」這個動作(商品目錄不在本規格範圍,SPEC.md L224), 故送不出調價那一步。代理:以 TWD 100.00 成立訂單後,查列表仍為總金額 10000 (= 1 × 下單當時單價的複本)近似「調價後舊訂單金額不動」—— 實際上只證明了「訂單保存的是下單當時的單價複本」,沒證明調價之後。 */
    @Test
    @DisplayName("S10: Given 商品「藍色馬克杯」單價為 TWD 100.00,客人 C-007 於該價格下單 1 個、訂單成立、 總金額 TWD 100.00;之後該商品單價被調整為 TWD 120.00,而後重新查看那筆舊訂單 Then 該訂單明細的單價仍顯示 TWD 100.00,總金額仍為 TWD 100.00")
    void scenario_S10() {
        ResponseEntity<String> resS10Order = placeOrder("""
                {"customerId":"C-007","items":[
                  {"productId":"P-MUG-BLUE","quantity":1,"unitPriceCents":10000,"currency":"TWD"}
                ]}""");
        String idS10Order = orderIdOf(resS10Order);
        Map<String, Object> rowS10Order = findInList(idS10Order);

        assertThat(resS10Order.getStatusCode().value())
                .isEqualTo(201);
        assertThat(rowS10Order).as("列表中找不到訂單 %s", idS10Order).isNotNull();
        assertThat(((Number) rowS10Order.get("totalCents")).longValue())
                .isEqualTo(10000L);
        assertThat(rowS10Order.get("currency"))
                .isEqualTo("TWD");
    }


    /** S12 —— 來源:本案自決 本案自決 — SPEC.md L119-L124(情境 S12,明示不是需求方說的); 依據 L246 ASSUMPTIONS「下單寫入為原子操作,不留半筆」與 C9 L186 / C11 L188
     * <p>⚠️ 代理編碼(綠了不等於原文成立):schema 沒有「在持久化中途注入故障」這個動作,送不出中斷那一步。 代理:正常成立同一筆訂單,以列表該列存在、且總金額 30000 與明細 Σ(數量 × 單價) 一致近似「不留下對不上的殘骸」—— 只覆蓋「完整成立」那一半,「故障後完全不存在」那一半本檔證明不了。 */
    @Test
    @DisplayName("S12: Given 客人 C-008 已登入,購物內容為「藍色馬克杯」2 個、單價 TWD 150.00; 他送出訂單,系統在持久化過程中(訂單主檔已寫、明細尚未寫完)發生故障中斷 Then 系統中不存在這筆訂單的任何部分 —— 不得留下沒有明細的訂單主檔, 也不得留下總金額與明細對不上的殘骸。要嘛完整成立,要嘛完全不存在")
    void scenario_S12() {
        ResponseEntity<String> resS12Order = placeOrder("""
                {"customerId":"C-008","items":[
                  {"productId":"P-MUG-BLUE","quantity":2,"unitPriceCents":15000,"currency":"TWD"}
                ]}""");
        String idS12Order = orderIdOf(resS12Order);
        Map<String, Object> rowS12Order = findInList(idS12Order);

        assertThat(resS12Order.getStatusCode().value())
                .isEqualTo(201);
        assertThat(idS12Order).isNotBlank();
        assertThat(rowS12Order).as("列表中找不到訂單 %s", idS12Order).isNotNull();
        assertThat(((Number) rowS12Order.get("totalCents")).longValue())
                .isEqualTo(30000L);
        assertThat(rowS12Order.get("status"))
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
