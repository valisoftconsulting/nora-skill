"""Tests del robot mínimo — sin plataforma (nora_helpers degrada solo).

Corre con:  python -m pytest tests/ -q
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

import main  # noqa: E402


def test_falla_sin_argumento_requerido():
    # Sin NORA_INPUT, get_input("mes") devuelve None → SystemExit(1)
    with pytest.raises(SystemExit) as exc:
        main.main()
    assert exc.value.code == 1


def test_corre_con_inputs(monkeypatch):
    import nora_helpers

    monkeypatch.setattr(
        nora_helpers, "get_input",
        lambda name=None, default=None: {"mes": "2026-07", "modo_prueba": True}.get(name, default),
    )
    salidas: dict = {}
    monkeypatch.setattr(nora_helpers, "set_output", lambda k, v: salidas.update({k: v}))
    main.main()
    assert salidas["procesados"] == 0
    assert "2026-07" in salidas["resumen"]
