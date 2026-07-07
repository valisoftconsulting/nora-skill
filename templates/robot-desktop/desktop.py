"""Aplicación de escritorio Windows vía pywinauto (backend UIA).

Reglas de oro del RPA de escritorio en NORA:
- backend="uia" SIEMPRE (el legacy win32 no ve apps modernas).
- Nada de sleeps fijos: usa wait("ready"/"visible") con timeout.
- La sesión de la máquina NORA corre por RDP a la resolución configurada
  (NORA_DISPLAY_WIDTH/HEIGHT) — no dependas de coordenadas absolutas; usa
  selectores de UIA (title/auto_id/control_type).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # solo type hints — los tests corren sin pywinauto
    from pywinauto import Application, WindowSpecification


@contextmanager
def open_app(exe_path: str, window_title_re: str, timeout: int = 30):
    """Abre (o conecta a) la app y entrega su ventana principal lista.

    Se cierra SIEMPRE al salir (también ante excepción).
    """
    from pywinauto import Application

    app: Application | None = None
    try:
        try:  # ¿ya está corriendo? conectar en vez de abrir otra instancia
            app = Application(backend="uia").connect(title_re=window_title_re, timeout=3)
        except Exception:
            app = Application(backend="uia").start(exe_path)
        window: WindowSpecification = app.window(title_re=window_title_re)
        window.wait("ready", timeout=timeout)
        yield window
    finally:
        if app is not None:
            try:
                app.kill()
            except Exception:
                pass
