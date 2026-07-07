"""Lógica de negocio web por transacción — ESTE es el archivo que editas.

`process_transaction(page, data, context)` recibe la página Playwright ya
abierta, el data del item y el context de `initialize()`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # solo para type hints — los tests corren sin playwright
    from playwright.sync_api import Page


class BusinessError(Exception):
    """Dato inválido — terminal, no se reintenta."""


def initialize(nora, page: Page, context: dict) -> None:
    """Navega/loguea UNA vez antes del loop (la sesión se reutiliza por item).

    context ya trae: context["url"] y, si existe el asset, context["cred"]
    ({username, value}).
    """
    page.goto(context["url"])
    # Ejemplo de login:
    # cred = context.get("cred")
    # if cred:
    #     page.fill("#usuario", cred["username"])
    #     page.fill("#password", cred["value"])
    #     page.click("#entrar")
    #     page.wait_for_selector("#dashboard")


def process_transaction(page: Page, data: dict, context: dict) -> dict:
    """Procesa UN item contra la web. Lanza BusinessError para datos inválidos;
    deja propagar timeouts/selectores rotos (error de sistema → reintenta)."""
    # === TU LÓGICA AQUÍ ===
    # if not data.get("numero"):
    #     raise BusinessError("Registro sin número")
    # page.fill("#numero", data["numero"])
    # page.click("#registrar")
    # page.wait_for_selector(".confirmacion")
    return {"status": "ok"}
