#!/usr/bin/env python3
"""Diagnóstico del entorno de desarrollo/operación NORA — falla temprano.

Uso:
    doctor.py [--offline]

Chequea, con remedio por ítem: Python, nora-sdk + CLI, sesión de `nora login`,
NORA_API_KEY (validez y scopes reales contra el backend), máquinas online y
Playwright (informativo). Exit 0 = todo lo esencial OK · 1 = hay bloqueantes.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nora_api  # noqa: E402

OK, WARN, FAIL = "✓", "⚠", "✗"
resultados: list[tuple[str, str, str]] = []  # (icono, chequeo, detalle/remedio)
bloqueantes = 0


def check(icono: str, nombre: str, detalle: str) -> None:
    global bloqueantes
    resultados.append((icono, nombre, detalle))
    if icono == FAIL:
        bloqueantes += 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--offline", action="store_true", help="sin llamadas de red")
    args = parser.parse_args()

    # 1. Python
    if sys.version_info >= (3, 10):
        check(OK, "Python", f"{sys.version.split()[0]} (≥ 3.10)")
    else:
        check(FAIL, "Python", f"{sys.version.split()[0]} — NORA requiere ≥ 3.10")

    # 2. nora-sdk + CLI
    try:
        import nora_agent
        version = getattr(nora_agent, "__version__", "?")
        check(OK, "nora-sdk", f"instalado (v{version})")
    except ImportError:
        check(WARN, "nora-sdk", "no instalado — `pip install nora-sdk` (necesario para "
                                "nora dev run / package / release push)")
    if shutil.which("nora"):
        check(OK, "CLI nora", "en PATH")
    else:
        check(WARN, "CLI nora", "no está en PATH (viene con pip install nora-sdk)")

    # 3. Sesión de nora login
    if nora_api.SESSION_FILE.exists():
        if args.offline:
            check(OK, "Sesión nora login", f"{nora_api.SESSION_FILE} presente (sin validar: --offline)")
        else:
            token = nora_api._session_access_token()
            if token:
                check(OK, "Sesión nora login", "refresh válido (rotado y guardado)")
            else:
                check(WARN, "Sesión nora login", "el refresh no canjeó — corre `nora login` de nuevo")
    else:
        check(WARN, "Sesión nora login", "sin sesión — `nora login` (necesaria para "
                                         "release push y subcomandos solo-sesión)")

    # 4. NORA_API_KEY + scopes reales
    key = os.environ.get("NORA_API_KEY", "").strip()
    if not key:
        check(WARN, "NORA_API_KEY", "no definida — sin ella solo funcionan los subcomandos "
                                    "de sesión. Genera una en Settings → API Keys (Pro/Enterprise).")
    elif not key.startswith("nora_ak_"):
        check(FAIL, "NORA_API_KEY", "formato inesperado (debe empezar con nora_ak_)")
    elif args.offline:
        check(OK, "NORA_API_KEY", "definida (sin validar: --offline)")
    else:
        scopes_ok: list[str] = []
        # Sondas mínimas de lectura por scope (baratas, 1 página de 1)
        sondas = [
            ("processes:read", "GET", "/processes/list"),
            ("machines:read", "GET", "/machines/list"),
        ]
        for scope, metodo, ruta in sondas:
            try:
                nora_api.call_api_key(metodo, ruta, params={"page": 1, "limit": 1})
                scopes_ok.append(scope)
            except nora_api.NoraError as e:
                if str(e).startswith("HTTP 403"):
                    pass  # sin ese scope
                elif str(e).startswith("HTTP 401"):
                    check(FAIL, "NORA_API_KEY", "el backend la rechaza (revocada/expirada)")
                    break
                else:
                    check(WARN, "NORA_API_KEY", f"no pude sondear {ruta}: {e}")
                    break
        else:
            if scopes_ok:
                check(OK, "NORA_API_KEY", f"válida; scopes de lectura confirmados: {', '.join(scopes_ok)}")
            else:
                check(WARN, "NORA_API_KEY", "válida pero sin processes:read ni machines:read — "
                                            "revisa los scopes de la key")

    # 5. Máquinas online (necesita alguna credencial y red)
    if not args.offline:
        try:
            result = nora_api.call("GET", "/machines/list",
                                   params={"page": 1, "limit": 100},
                                   session_path="/machines")
            maquinas = result["data"] if isinstance(result, dict) else result
            online = [m["name"] for m in maquinas if m.get("status") in ("online", "busy")]
            if online:
                check(OK, "Máquinas online", ", ".join(online[:5]) + ("…" if len(online) > 5 else ""))
            else:
                check(WARN, "Máquinas online", "ninguna — los jobs quedarán pending. "
                                               "Instala/enciende un agente (consola → Máquinas).")
        except nora_api.NoraError as e:
            check(WARN, "Máquinas online", f"no pude consultar: {e}")

    # 6. Playwright (informativo, solo si el robot lo usa)
    try:
        import playwright  # noqa: F401
        check(OK, "Playwright", "instalado (recuerda `python -m playwright install chromium`)")
    except ImportError:
        check(WARN, "Playwright", "no instalado — solo necesario para robots web (robot-browser)")

    ancho = max(len(n) for _, n, _ in resultados)
    for icono, nombre, detalle in resultados:
        print(f" {icono} {nombre.ljust(ancho)}  {detalle}", file=sys.stderr)
    print(json.dumps(
        {"ok": bloqueantes == 0,
         "checks": [{"status": i, "name": n, "detail": d} for i, n, d in resultados]},
        ensure_ascii=False, indent=2,
    ))
    sys.exit(1 if bloqueantes else 0)


if __name__ == "__main__":
    main()
