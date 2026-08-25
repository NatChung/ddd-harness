# examples/shop/tests

這裡的測試量的是 **harness/ 各檢查器在 shop 凍結語料上的行為**(數字逐份釘死:
`examples/shop/harness/runs/**`、`examples/shop/app/`、`examples/shop/spec/`,
以及 `examples/returns/interview-prompt.md` 那份凍結受測品)。

它們原本住在 `harness/test_*.py`,2026-08-26 搬到這裡(票 32):hub 是整包複製
`harness/` 過去的,不帶 `examples/`,語料測試留在 harness/ 裡到了 hub 就全紅。
搬過來的測試逐字不改;helper 從 harness 那邊的同名測試檔 import(`conftest.py`
把 `<repo>/harness` 放進 sys.path)。檔名加 `corpus_` 前綴是為了避開 pytest
同 basename 的 import 衝突(`harness/test_glossary.py` vs 這裡的)。

跑法(repo root):`python3 -m pytest examples/shop/tests -q -p no:cacheprovider`
