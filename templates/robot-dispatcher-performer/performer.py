"""Performer: consume la cola item por item (loop transaccional).

Editas `process_item()` — el resto del loop (claim, clasificación de errores,
progreso, stop) ya está resuelto en `run()`.
"""

from __future__ import annotations

import nora_helpers as nora
from config import QUEUE


class BusinessError(Exception):
    """Dato inválido — terminal, no se reintenta."""


def process_item(data: dict) -> dict:
    """Procesa UN item y devuelve el result.

    Lanza BusinessError para datos inválidos; deja propagar el resto (se
    tratan como error de sistema y la plataforma reintenta).
    """
    # === TU LÓGICA AQUÍ ===
    return {"status": "ok"}


def run(max_items: int = 0) -> dict:
    """Loop transaccional. Devuelve contadores para los outputs del job."""
    total = nora.pending(QUEUE)
    nora.log("info", f"Performer: {total} items pendientes en '{QUEUE}'.")

    procesados = fallidos_negocio = fallidos_sistema = 0
    while True:
        if nora.should_stop():
            nora.log("warning", "Stop solicitado — cierre ordenado.")
            break
        if max_items and procesados + fallidos_negocio + fallidos_sistema >= max_items:
            break

        item = nora.claim_next(QUEUE)
        if item is None:
            break

        ref = item.get("reference") or item.get("id")
        try:
            result = process_item(item.get("data") or {})
            nora.complete(QUEUE, item, result)
            procesados += 1
        except BusinessError as e:
            nora.fail_business(QUEUE, item, str(e))
            fallidos_negocio += 1
            nora.log("warning", f"Excepción de negocio en {ref}: {e}")
        except Exception as e:
            nora.fail_system(QUEUE, item, str(e))
            fallidos_sistema += 1
            nora.log("error", f"Excepción de sistema en {ref}: {e}")

        hechos = procesados + fallidos_negocio + fallidos_sistema
        if total:
            nora.progress(min(int(hechos * 100 / total), 99), f"{hechos}/{total} items")

    return {
        "procesados": procesados,
        "fallidos_negocio": fallidos_negocio,
        "fallidos_sistema": fallidos_sistema,
    }
