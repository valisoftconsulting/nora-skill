"""Lógica de negocio de escritorio por transacción — ESTE es el archivo que editas.

`process_transaction(window, data, context)` recibe la ventana principal
(pywinauto WindowSpecification, backend uia), el data del item y el context.
"""

from __future__ import annotations


class BusinessError(Exception):
    """Dato inválido — terminal, no se reintenta."""


def process_transaction(window, data: dict, context: dict) -> dict:
    """Procesa UN item contra la app. Lanza BusinessError para datos inválidos;
    deja propagar timeouts de UIA (error de sistema → la plataforma reintenta).

    Patrón pywinauto (backend uia):
        window.child_window(auto_id="txtNumero", control_type="Edit").set_text(...)
        window.child_window(title="Registrar", control_type="Button").click_input()
        window.child_window(auto_id="lblConfirmacion").wait("visible", timeout=15)
    Inspecciona selectores con inspect.exe (Windows SDK) o py -m pywinauto.recorder.
    """
    # === TU LÓGICA AQUÍ ===
    # if not data.get("numero"):
    #     raise BusinessError("Registro sin número")
    return {"status": "ok"}
