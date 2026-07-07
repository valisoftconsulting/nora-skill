"""Robot mínimo NORA: argumentos in/out, logging y progreso.

Prueba local:      python main.py
Prueba real (dev): nora dev run main.py --input '{"mes": "2026-07"}'
"""

import nora_helpers as nora


def main() -> None:
    mes = nora.get_input("mes")
    modo_prueba = nora.get_input("modo_prueba", False)

    if not mes:
        nora.log("error", "Falta el argumento requerido 'mes' (YYYY-MM).")
        raise SystemExit(1)

    nora.log("info", f"Inicio: mes={mes} modo_prueba={modo_prueba}")
    nora.progress(10, "Preparando")

    # === TU LÓGICA AQUÍ ===
    procesados = 0
    nora.progress(90, "Cerrando")

    nora.set_output("procesados", procesados)
    nora.set_output("resumen", f"Mes {mes}: {procesados} registros procesados.")
    nora.progress(100, "Listo")
    nora.log("info", "Fin OK.")


if __name__ == "__main__":
    main()
