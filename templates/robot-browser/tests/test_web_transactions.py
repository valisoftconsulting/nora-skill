"""Tests unitarios — sin plataforma NI navegador real (Page fake).

Corre con:  python -m pytest tests/ -q
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from transactions import BusinessError, process_transaction  # noqa: E402


class FakePage:
    """Doble mínimo de playwright Page: registra acciones, no abre nada."""

    def __init__(self):
        self.acciones: list[tuple] = []

    def goto(self, url, **kw):
        self.acciones.append(("goto", url))

    def fill(self, selector, valor, **kw):
        self.acciones.append(("fill", selector, valor))

    def click(self, selector, **kw):
        self.acciones.append(("click", selector))

    def wait_for_selector(self, selector, **kw):
        self.acciones.append(("wait", selector))


def test_process_transaction_ok():
    page = FakePage()
    result = process_transaction(page, {"campo": "valor"}, {"url": "https://example.com"})
    assert isinstance(result, dict)


def test_business_error_is_raisable():
    with pytest.raises(BusinessError):
        raise BusinessError("Registro sin número")
