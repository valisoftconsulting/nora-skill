"""Tests unitarios de dispatcher/performer — SIN plataforma.

Corre con:  python -m pytest tests/ -q
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

import dispatcher  # noqa: E402
from performer import BusinessError, process_item  # noqa: E402


def test_to_queue_item_is_serializable():
    record = {"id": "1", "monto": 100}
    item = dispatcher.to_queue_item(record)
    assert isinstance(item, dict)


def test_process_item_ok():
    result = process_item({"campo": "valor"})
    assert isinstance(result, dict)


def test_business_error_is_raisable():
    with pytest.raises(BusinessError):
        raise BusinessError("Registro inválido")
