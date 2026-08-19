package com.shop.adapter.persistence;

import org.springframework.data.jpa.repository.JpaRepository;

/** Spring Data 的儲存介面 —— 純粹是 adapter 的細節。 */
public interface SpringDataOrderRepository extends JpaRepository<OrderJpaEntity, String> {
}
