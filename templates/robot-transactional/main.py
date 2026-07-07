"""Robot transaccional NORA — mismas fases que el REFramework de UiPath:

    initialize → get_next_transaction → process_transaction → end

El loop reclama items de la cola uno a uno, clasifica errores en
negocio/sistema y deja los reintentos en manos de la plataforma (max_retries
de la cola). NO reimplementes reintentos aquí.

Prueba local:      python main.py           (sin credenciales: no hay cola, termina limpio)
Prueba real (dev): nora dev run main.py
"""

import nora_helpers as nora
from config import QUEUE
from transactions import BusinessError, end, initialize, process_transaction


def main() -> None:
    max_items = int(nora.get_input("max_items", 0) or 0)
    total = nora.pending(QUEUE)
    nora.log("info", f"Inicio. Items pendientes en '{QUEUE}': {total}")

    context = initialize(nora)
    procesados = fallidos_negocio = fallidos_sistema = 0

    try:
        while True:
            if nora.should_stop():
                nora.log("warning", "Stop solicitado desde el dashboard — cierre ordenado.")
                break
            if max_items and procesados + fallidos_negocio + fallidos_sistema >= max_items:
                nora.log("info", f"Límite max_items={max_items} alcanzado.")
                break

            item = nora.claim_next(QUEUE)
            if item is None:
                nora.log("info", "Cola vacía — no hay más transacciones.")
                break

            ref = item.get("reference") or item.get("id")
            try:
                result = process_transaction(item.get("data") or {}, context)
                nora.complete(QUEUE, item, result)
                procesados += 1
                nora.log("info", f"Transacción OK: {ref}")
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
    finally:
        end(nora, context)

    nora.set_output("procesados", procesados)
    nora.set_output("fallidos_negocio", fallidos_negocio)
    nora.set_output("fallidos_sistema", fallidos_sistema)
    nora.set_output(
        "resumen",
        f"OK={procesados} negocio={fallidos_negocio} sistema={fallidos_sistema}",
    )
    nora.progress(100, "Listo")
    nora.log("info", "Fin.")


if __name__ == "__main__":
    main()
