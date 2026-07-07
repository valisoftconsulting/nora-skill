"""Dispatcher: lee la fuente de datos y puebla la cola.

Editas `fetch_records()` (de dónde salen los registros) y, si hace falta,
`to_queue_item()` (cómo se transforma cada registro en payload del item).
"""

from __future__ import annotations

import nora_helpers as nora
from config import QUEUE, REFERENCE_FIELD


def fetch_records() -> list[dict]:
    """Obtiene los registros a procesar (CSV, API, BD, Excel...).

    Cada registro debe ser un dict serializable a JSON.
    """
    # === TU FUENTE AQUÍ ===
    # import csv
    # with open("data/pendientes.csv", newline="", encoding="utf-8") as f:
    #     return list(csv.DictReader(f))
    return []


def to_queue_item(record: dict) -> dict:
    """Transforma un registro fuente en el payload del queue item."""
    return record


def run() -> int:
    """Encola los registros con dedupe por reference. Devuelve cuántos encoló."""
    records = fetch_records()
    nora.log("info", f"Dispatcher: {len(records)} registros en la fuente.")

    encolados = 0
    for record in records:
        reference = str(record.get(REFERENCE_FIELD, "")) or None
        if nora.enqueue_one(QUEUE, to_queue_item(record), reference=reference):
            encolados += 1

    nora.log("info", f"Dispatcher: {encolados} items encolados en '{QUEUE}'.")
    return encolados
