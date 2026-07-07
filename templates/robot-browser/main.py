"""Robot web NORA: Playwright + cola transaccional.

El navegador se abre UNA vez (viewport = resolución de la sesión de la
máquina) y se procesan los items de la cola contra la misma sesión web.

Prueba local:      python main.py                (sin credenciales: termina limpio)
Prueba real (dev): nora dev run main.py --assets APP_URL,APP_CREDENCIALES -e dev
Nota: requiere `playwright install chromium` una vez por máquina.
"""

import nora_helpers as nora
from browser import open_page
from config import CRED_ASSET, QUEUE, URL_ASSET, URL_FALLBACK
from transactions import BusinessError, initialize, process_transaction


def main() -> None:
    max_items = int(nora.get_input("max_items", 0) or 0)
    headless = bool(nora.get_input("headless", True))

    url_asset = nora.asset(URL_ASSET)
    context = {
        "url": (url_asset or {}).get("value") or URL_FALLBACK,
        "cred": nora.asset(CRED_ASSET),
    }

    total = nora.pending(QUEUE)
    nora.log("info", f"Inicio. URL={context['url']} pendientes={total} headless={headless}")
    procesados = fallidos_negocio = fallidos_sistema = 0

    with open_page(headless=headless) as page:
        initialize(nora, page, context)

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
                result = process_transaction(page, item.get("data") or {}, context)
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
