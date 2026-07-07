"""Navegador Playwright alineado a la sesión de la máquina NORA.

El agente inyecta NORA_DISPLAY_WIDTH/HEIGHT (resolución de la sesión). Fijar
el viewport a esos valores hace que los selectores y screenshots sean
estables entre tu máquina y las máquinas del orquestador.
"""

from __future__ import annotations

import os
from contextlib import contextmanager

from playwright.sync_api import Browser, Page, sync_playwright


def session_viewport() -> dict:
    return {
        "width": int(os.environ.get("NORA_DISPLAY_WIDTH", 1920)),
        "height": int(os.environ.get("NORA_DISPLAY_HEIGHT", 1080)),
    }


@contextmanager
def open_page(headless: bool = True):
    """Context manager: navegador + página con el viewport de la sesión.

    Uso:
        with open_page(headless=True) as page:
            page.goto(url)
    Se cierra SIEMPRE (también ante excepción) — nada de navegadores zombis.
    """
    with sync_playwright() as pw:
        browser: Browser = pw.chromium.launch(headless=headless)
        try:
            context = browser.new_context(viewport=session_viewport())
            page: Page = context.new_page()
            page.set_default_timeout(30_000)
            yield page
        finally:
            browser.close()
