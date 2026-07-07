#!/usr/bin/env python3
"""Gestiona máquinas de NORA: alta, listado y versión de la flota.

Uso:
    nora_machine.py create --name "PC-Contabilidad" [--max-concurrent 2]
    nora_machine.py list [--status online|offline|busy]
    nora_machine.py fleet-version

`create` (sesión, rol admin) da de alta la máquina y muestra su machine_key
UNA sola vez — guárdala; luego descarga el agente de esa máquina desde la
consola (Máquinas → Descargar agente: el zip ya trae la key y el instalador).
`fleet-version` muestra la versión current del agente y qué versión reporta
cada máquina (las que digan null son pre-0.8.0 → necesitan una reinstalación
manual única para entrar al auto-update).
Scopes: machines:read (list). create/fleet-version: sesión de `nora login`.
"""

import argparse

import nora_api


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_create = sub.add_parser("create", help="dar de alta una máquina (sesión, admin)")
    p_create.add_argument("--name", required=True)
    p_create.add_argument("--max-concurrent", type=int, default=1,
                          help="jobs concurrentes que acepta la máquina")

    p_list = sub.add_parser("list", help="listar máquinas")
    p_list.add_argument("--status", choices=["online", "offline", "busy"])
    p_list.add_argument("--page", type=int, default=1)
    p_list.add_argument("--limit", type=int, default=50, choices=range(1, 101), metavar="1-100")

    sub.add_parser("fleet-version", help="versión current vs versión reportada por máquina")

    args = parser.parse_args()

    if args.cmd == "create":
        # El alta solo acepta `name`; la concurrencia se fija con un PUT
        # posterior (el backend descarta campos extra en la creación).
        machine = nora_api.call_session("POST", "/machines", body={"name": args.name})
        if args.max_concurrent != 1:
            nora_api.call_session(
                "PUT", f"/machines/{nora_api.seg(machine['id'])}",
                body={"max_concurrent_jobs": args.max_concurrent},
            )
            machine["max_concurrent_jobs"] = args.max_concurrent
        nora_api.eprint(
            "Máquina creada. GUARDA LA machine_key AHORA — no se vuelve a mostrar\n"
            "completa. Siguiente paso: consola → Máquinas → Descargar agente (el\n"
            "zip ya incluye la key y el instalador para Windows/macOS)."
        )
        nora_api.emit(machine)

    elif args.cmd == "list":
        params = {"page": args.page, "limit": args.limit}
        if args.status:
            params["status"] = args.status
        result = nora_api.call("GET", "/machines/list", params=params, session_path="/machines")
        nora_api.emit(result)

    elif args.cmd == "fleet-version":
        current = nora_api.call_session("GET", "/machines/agent-version/current")
        result = nora_api.call_session("GET", "/machines", params={"page": 1, "limit": 100})
        machines = result["data"] if isinstance(result, dict) else result
        fleet = [
            {
                "name": m["name"],
                "status": m["status"],
                "agent_version": (m.get("system_info") or {}).get("agent_version"),
            }
            for m in machines
        ]
        desactualizadas = [
            m["name"] for m in fleet
            if current.get("version") and m["agent_version"] != current["version"]
        ]
        nora_api.emit({
            "current": current.get("version"),
            "machines": fleet,
            "outdated_or_unknown": desactualizadas,
        })
        if desactualizadas:
            nora_api.eprint(
                f"{len(desactualizadas)} máquina(s) fuera de la versión current. Las que "
                "reportan null son pre-0.8.0: requieren UNA reinstalación manual; el "
                "resto convergerá solo (chequeo cada ~30 min, drena sin cortar jobs)."
            )


if __name__ == "__main__":
    nora_api.run(main)
