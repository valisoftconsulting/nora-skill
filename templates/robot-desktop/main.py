"""Robot de escritorio Windows NORA: pywinauto (UIA) + cola transaccional.

La app se abre UNA vez y se procesan los items de la cola contra la misma
sesión. Corre en la sesión RDP de la máquina NORA a la resolución configurada.

Prueba real (dev): nora dev run main.py  (en una máquina Windows con la app)
Nota: pywinauto requiere Windows; los tests unitarios corren en cualquier SO.
"""

import nora_helpers as nora
from config import APP_PATH_ASSET, APP_PATH_FALLBACK, MAIN_WINDOW_TITLE, QUEUE
from desktop import open_app
from transactions import BusinessError, process_transaction


def main() -> None:
    max_items = int(nora.get_input("max_items", 0) or 0)

    path_asset = nora.asset(APP_PATH_ASSET)
    exe_path = (path_asset or {}).get("value") or APP_PATH_FALLBACK
    context: dict = {}

    total = nora.pending(QUEUE)
    nora.log("info", f"Inicio. app={exe_path} pendientes={total}")
    procesados = fallidos_negocio = fallidos_sistema = 0

    with open_app(exe_path, MAIN_WINDOW_TITLE) as window:
        while True:
            if nora.should_stop():
                nora.log("warning", "Stop solicitado — cierre ordenado.")
                break
            if max_items and procesados + fallidos_negocio + fallidos_sistema >= max_items:
                break

            item = nora.claim_next(QUEUE)
            if item is None:
                nora.log("info", "Cola vacía.")
                break

            ref = item.get("reference") or item.get("id")
            try:
                result = process_transaction(window, item.get("data") or {}, context)
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

    nora.set_output("procesados", procesados)
    nora.set_output("fallidos_negocio", fallidos_negocio)
    nora.set_output("fallidos_sistema", fallidos_sistema)
    nora.progress(100, "Listo")
    nora.log("info", f"Fin. OK={procesados} negocio={fallidos_negocio} sistema={fallidos_sistema}")


if __name__ == "__main__":
    main()
