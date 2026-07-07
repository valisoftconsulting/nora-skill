"""Tests unitarios de la lógica de negocio — SIN plataforma.

`process_transaction` recibe data y context planos, así que se prueba con
pytest puro. `initialize`/`end` reciben un fake de nora_helpers para no tocar
red. Corre con:  python -m pytest tests/ -q
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from transactions import BusinessError, end, initialize, process_transaction  # noqa: E402


class FakeNora:
    """Doble de nora_helpers: registra llamadas, no toca la plataforma."""

    def __init__(self, assets: dict | None = None):
        self.assets = assets or {}
        self.logs: list[tuple] = []

    def asset(self, name, environment="production"):
        return self.assets.get(name)

    def log(self, level, message, data=None):
        self.logs.append((level, message, data))


def test_process_transaction_ok():
    context = initialize(FakeNora())
    result = process_transaction({"campo": "valor"}, context)
    assert isinstance(result, dict)


def test_initialize_and_end_do_not_crash():
    fake = FakeNora()
    context = initialize(fake)
    end(fake, context)


def test_business_error_is_raisable():
    # Ejemplo de contrato: cuando agregues validaciones, prueba que los datos
    # inválidos lanzan BusinessError (terminal) y no una excepción genérica.
    with pytest.raises(BusinessError):
        raise BusinessError("Factura sin RUC")
