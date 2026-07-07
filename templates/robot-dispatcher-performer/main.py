"""Robot dispatcher+performer NORA — un solo paquete, tres modos vía input:

- mode=dispatcher : solo puebla la cola desde la fuente.
- mode=performer  : solo consume la cola (puedes correr varios en paralelo).
- mode=auto       : si la cola está vacía hace dispatch, y luego procesa.

Para escalar: crea DOS procesos desde la misma release (uno con input fijo
dispatcher, otro performer) y lanza N jobs performer en máquinas distintas.

Prueba local:      python main.py
Prueba real (dev): nora dev run main.py --input '{"mode": "auto"}'
"""

import dispatcher
import nora_helpers as nora
import performer
from config import QUEUE


def main() -> None:
    mode = str(nora.get_input("mode", "auto") or "auto").lower()
    max_items = int(nora.get_input("max_items", 0) or 0)
    nora.log("info", f"Inicio en modo '{mode}'.")

    encolados = 0
    stats = {"procesados": 0, "fallidos_negocio": 0, "fallidos_sistema": 0}

    if mode == "dispatcher":
        encolados = dispatcher.run()
    elif mode == "performer":
        stats = performer.run(max_items)
    elif mode == "auto":
        if nora.pending(QUEUE) == 0:
            encolados = dispatcher.run()
        stats = performer.run(max_items)
    else:
        nora.log("error", f"Modo desconocido: '{mode}'. Usa dispatcher|performer|auto.")
        raise SystemExit(1)

    nora.set_output("encolados", encolados)
    for key, value in stats.items():
        nora.set_output(key, value)
    nora.progress(100, "Listo")
    nora.log("info", f"Fin. encolados={encolados} {stats}")


if __name__ == "__main__":
    main()
