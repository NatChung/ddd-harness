# Order 成立即鎖定,不提供修改與取消

Stakeholder 明確要求「成立就鎖定」,且取消/修改功能「先不用,以後再說」(INTERVIEW-LOG Q9、Q10)。因此 Order 為 immutable:成立後不提供任何變更內容或取消的操作,也不設計對應 API;訂單有錯的補救方式(例如重下一張)留待未來需求出現再決定。記錄原因:這是範圍邊界的 explicit no——immutability 決定了資料模型與 API 的形狀,若日後有人想「補一個編輯功能」,必須先回到這個決定。
