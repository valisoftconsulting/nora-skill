"""Tests unitarios — sin Windows NI pywinauto (Window fake).

Corre con:  python -m pytest tests/ -q
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from transactions import BusinessError, process_transaction  # noqa: E402


class FakeControl:
    def __init__(self, registro):
        self._registro = registro

    def set_text(self, valor, **kw):
        self._registro.append(("set_text", valor))

    def click_input(self, **kw):
        self._registro.append(("click",))

    def wait(self, estado, **kw):
        self._registro.append(("wait", estado))


class FakeWindow:
    """Doble mínimo de WindowSpecification: registra acciones."""

    def __init__(self):
        self.acciones: list[tuple] = []

    def child_window(self, **criterios):
        self.acciones.append(("child_window", tuple(sorted(criterios.items()))))
        return FakeControl(self.acciones)


def test_process_transaction_ok():
    window = FakeWindow()
    result = process_transaction(window, {"campo": "valor"}, {})
    assert isinstance(result, dict)


def test_business_error_is_raisable():
    with pytest.raises(BusinessError):
        raise BusinessError("Registro sin número")
