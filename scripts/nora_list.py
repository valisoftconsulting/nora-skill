#!/usr/bin/env python3
"""Lista recursos del orquestador NORA.

Uso:
    nora_list.py machines|processes [--page 1] [--limit 50]
    nora_list.py queues|schedules|jobs|triggers [--page 1] [--limit 50]

machines/processes: API key (scopes machines:read / processes:read) con
fallback a sesión. queues/schedules/jobs/triggers: SOLO sesión de `nora login`
(endpoints internos de la consola).
"""

import argparse

import nora_api

# recurso → (path API key, path sesión). None = esa vía no existe.
RUTAS = {
    "machines": ("/machines/list", "/machines"),
    "processes": ("/processes/list", "/processes"),
    "queues": (None, "/queues"),
    "schedules": (None, "/schedules"),
    "jobs": (None, "/jobs"),
    "triggers": (None, "/triggers"),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("recurso", choices=sorted(RUTAS))
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    api_path, session_path = RUTAS[args.recurso]
    params = {"page": args.page, "limit": args.limit}
    if args.recurso == "triggers":
        params = None  # el listado de triggers no pagina

    if api_path:
        result = nora_api.call("GET", api_path, params=params, session_path=session_path)
    else:
        result = nora_api.call_session("GET", session_path, params=params)
    nora_api.emit(result)


if __name__ == "__main__":
    nora_api.run(main)
