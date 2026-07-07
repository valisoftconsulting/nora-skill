"""Acceso a NORA (Robots Center) — TODO el trato con la plataforma vive aquí.

Copia este archivo dentro de tu robot y llama a estas funciones desde tu
lógica: `log(...)`, `claim_next(...)`, `fail_business(...)`, etc. Así tus
workflows quedan limpios y no saben de HTTP ni del SDK.

Funciona con o sin SDK instalado: si `nora_agent` no está disponible (ejecución
fuera de NORA), `log()` imprime por consola, `get_input()` usa defaults y las
operaciones de cola avisan en lugar de romper. Eso permite probar el robot con
`python main.py` antes de tener credenciales.

Fuente canónica: https://github.com/valisoftconsulting/nora-skill
(templates/nora_helpers.py). No edites esta copia a mano: si necesitas más
capacidades, usa el SDK (`from nora_agent import sdk`) desde aquí.
"""

from __future__ import annotations

try:
    from nora_agent import sdk
except Exception:  # pragma: no cover - sin SDK instalado
    sdk = None


# --- Argumentos de entrada / salida ---------------------------------------------

def get_input(name: str | None = None, default=None):
    """Lee un argumento de entrada del job (o todos si name es None)."""
    if not sdk:
        return default if name else {}
    try:
        return sdk.get_input(name, default) if name else sdk.get_inputs()
    except Exception:
        return default if name else {}


def set_output(key: str, value) -> None:
    """Publica un argumento de salida del job (merge server-side)."""
    if not sdk:
        print(f"[output] {key} = {value!r}")
        return
    try:
        sdk.set_output(key, value)
    except Exception as e:
        log("warning", f"set_output('{key}') falló: {e}")


# --- Logs / progreso -------------------------------------------------------------

def log(level: str, message: str, data: dict | None = None) -> None:
    try:
        if sdk:
            sdk.log(level, message, data)
            return
    except Exception:
        pass
    print(f"[{level.upper()}] {message}" + (f" {data}" if data else ""))


def progress(percent: int, message: str) -> None:
    try:
        if sdk:
            sdk.update_progress(percent, message)
            return
    except Exception:
        pass
    print(f"[progress] {percent}% - {message}")


# --- Cola --------------------------------------------------------------------------

def pending(queue: str) -> int:
    """Cuántos items quedan por procesar (status 'new'), sin consumir nada."""
    if not sdk:
        return 0
    try:
        return sdk.queue_pending(queue)
    except Exception as e:
        log("warning", f"No pude consultar la cola '{queue}': {e}")
        return 0


def enqueue(queue: str, records: list[dict]) -> int:
    """Carga registros en la cola (bulk). Devuelve cuántos."""
    if not sdk:
        log("error", "Sin SDK/credenciales: no puedo cargar la cola.")
        return 0
    added = sdk.add_queue_items(queue, records)
    log("info", f"{added} items cargados en la cola '{queue}'.")
    return added


def enqueue_one(queue: str, record: dict, reference: str | None = None) -> dict | None:
    """Carga un único item. Usa `reference` como clave de idempotencia."""
    if not sdk:
        log("error", "Sin SDK/credenciales: no puedo encolar.")
        return None
    try:
        return sdk.add_queue_item(queue, record, reference=reference)
    except Exception as e:
        log("warning", f"enqueue_one falló: {e}")
        return None


def claim_next(queue: str) -> dict | None:
    """Reclama el siguiente item de la cola (o None si está vacía)."""
    if not sdk:
        return None
    try:
        return sdk.get_queue_item(queue)
    except Exception as e:
        log("warning", f"No pude reclamar item de '{queue}': {e}")
        return None


def complete(queue: str, item: dict, result: dict | None = None) -> None:
    """Marca un item como completado."""
    if sdk and item.get("id"):
        try:
            sdk.complete_queue_item(queue, item["id"], result or {})
        except Exception as e:
            log("warning", f"complete falló: {e}")


def fail_business(queue: str, item: dict, error: str) -> None:
    """Excepción de NEGOCIO: el dato es inválido. Terminal — NO se reintenta.

    Úsala cuando reintentar con los mismos datos jamás tendrá éxito
    (factura sin RUC, cliente inexistente, monto negativo...).
    """
    if sdk and item.get("id"):
        try:
            sdk.fail_queue_item(queue, item["id"], error, exception_type="business")
        except Exception:
            pass


def fail_system(queue: str, item: dict, error: str) -> None:
    """Excepción de SISTEMA: fallo transitorio (red, timeout, app caída).

    La plataforma reintenta el item hasta `max_retries` de la cola y luego lo
    manda a dead_letter.
    """
    if sdk and item.get("id"):
        try:
            sdk.fail_queue_item(queue, item["id"], error, exception_type="system")
        except Exception:
            pass


def send_for_review(queue: str, item: dict) -> None:
    """Manda un item a revisión humana (status -> pending_review)."""
    if sdk and item.get("id"):
        try:
            sdk.send_queue_item_for_review(queue, item["id"])
        except Exception as e:
            log("warning", f"send_for_review falló: {e}")


def wait_review(queue: str, item: dict, timeout: float = 3600.0) -> str:
    """Bloquea hasta que el operador apruebe/rechace. Devuelve 'approved' o
    'rejected' (o 'approved' si no hay SDK, para no bloquear en dev local)."""
    if not (sdk and item.get("id")):
        return "approved"
    try:
        return sdk.wait_for_queue_review(queue, item["id"], timeout=timeout)
    except Exception as e:
        log("warning", f"wait_review falló: {e}")
        return "rejected"


# --- Assets (credenciales/config cifradas) -----------------------------------------

def asset(name: str, environment: str = "production") -> dict | None:
    """Lee un asset descifrado por nombre: {name, type, environment, value, username?}."""
    if not sdk:
        log("warning", f"Sin SDK: no puedo leer el asset '{name}'.")
        return None
    try:
        return sdk.get_asset(name, environment)
    except Exception as e:
        log("warning", f"No pude leer el asset '{name}': {e}")
        return None


# --- Señal de control (Stop/Kill desde el dashboard) --------------------------------

def should_stop() -> bool:
    """True si el operador pidió detener el job — chequéalo dentro de tu bucle."""
    if not sdk:
        return False
    try:
        return sdk.should_stop()
    except Exception:
        return False


# --- Input atendido (human-in-the-loop) ----------------------------------------------

def ask_user(prompt: str, options: list[str] | None = None, timeout: float = 3600.0):
    """Pide un dato al operador y espera la respuesta (solo en job gestionado)."""
    if not sdk:
        log("warning", "Sin SDK: no puedo pedir input al operador.")
        return None
    try:
        return sdk.ask_user(prompt, options, timeout=timeout)
    except Exception as e:
        log("warning", f"ask_user falló: {e}")
        return None
