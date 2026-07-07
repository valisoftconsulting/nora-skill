"""Lógica de negocio por transacción — ESTE es el archivo que editas.

`process_transaction(data, context)` procesa UN item de la cola y devuelve un
dict con el resultado. Para clasificar errores usa las excepciones de abajo:

- `BusinessError`: el dato es inválido; reintentar jamás funcionará
  (factura sin RUC, cliente inexistente). El item queda `failed` terminal.
- Cualquier otra excepción se trata como error de SISTEMA (red, timeout, app
  caída): la plataforma reintenta el item hasta `max_retries` de la cola.

`context` trae recursos compartidos creados en `initialize()` (sesión de
navegador, credenciales, conexiones) para no recrearlos por item.
"""

from __future__ import annotations


class BusinessError(Exception):
    """Dato inválido — terminal, no se reintenta."""


def initialize(nora) -> dict:
    """Prepara recursos compartidos UNA vez (login, navegador, conexiones).

    Devuelve el `context` que recibirá cada transacción.
    """
    context: dict = {}
    # Ejemplo: credenciales desde un asset
    # cred = nora.asset("app_credenciales")
    # context["usuario"] = cred["username"]
    # context["password"] = cred["value"]
    return context


def process_transaction(data: dict, context: dict) -> dict:
    """Procesa UN item. Recibe `data` (el payload del item) y devuelve el result.

    Lanza BusinessError para datos inválidos; deja propagar el resto.
    """
    # === TU LÓGICA AQUÍ ===
    # if not data.get("ruc"):
    #     raise BusinessError("Factura sin RUC")
    return {"status": "ok"}


def end(nora, context: dict) -> None:
    """Libera recursos compartidos (cerrar navegador, sesiones, archivos)."""
    # Ejemplo: context["browser"].close()
    return None
