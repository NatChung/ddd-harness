"""examples/shop/tests 的 pytest 設定:把 `<repo>/harness` 放進 sys.path。

這裡的測試 import 的是 harness/ 底下的檢查器(`landing_check`、`spec_store`…)
與 harness 測試檔裡的 helper(`from test_glossary import run_check` 之類)。
harness/ 自己沒有 conftest —— pytest 收集 harness/test_*.py 時會自動把該目錄
prepend 進 sys.path;這一份只是替住在 harness/ 外面的測試補上同一件事。
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HARNESS = REPO / "harness"

if str(HARNESS) not in sys.path:
    sys.path.insert(0, str(HARNESS))
