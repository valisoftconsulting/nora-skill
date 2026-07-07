#!/usr/bin/env python3
"""Crea y gestiona procesos de NORA (cierra el ciclo release → proceso sin UI).

Uso:
    nora_process.py list [--page 1] [--limit 50]
    nora_process.py releases --package <nombre> [--version 1.2.3]
    nora_process.py create --name "Mi proceso" --release <paquete@version|release_id> \
        [--timeout 1800] [--max-retries 2] [--auto-retry] \
        [--assets ASSET1,ASSET2] [--tags a,b] [--description "..."]
    nora_process.py active <process_id> --on|--off
    nora_process.py set-release <process_id|nombre> --release <paquete@version|release_id>

Scopes: processes:read / processes:write. Fallback a sesión de `nora login`:
list, releases y create degradan; `active` es solo API key; `set-release` es
SOLO sesión (endpoint interno de promote/rollback de release).
"""

import argparse
import uuid as uuid_mod

import nora_api


def resolve_release_id(spec: str) -> str:
    """Acepta un UUID de release o 'paquete@version' (o 'paquete' = más reciente)."""
    try:
        return str(uuid_mod.UUID(spec))
    except ValueError:
        pass
    package, _, version = spec.partition("@")
    result = nora_api.call(
        "GET", "/releases/list",
        params={"package": package, "limit": 100},
        session_path="/releases",
    )
    releases = result["data"] if isinstance(result, dict) else result
    if version:
        for release in releases:
            if release["version"] == version:
                return release["id"]
        raise nora_api.NoraError(f"No hay release {version} del paquete '{package}'.", 1)
    if not releases:
        raise nora_api.NoraError(f"El paquete '{package}' no tiene releases.", 1)
    return releases[0]["id"]  # vienen ordenadas por fecha desc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="listar procesos activos")
    p_list.add_argument("--page", type=int, default=1)
    p_list.add_argument("--limit", type=int, default=50)

    p_rel = sub.add_parser("releases", help="listar releases de un paquete")
    p_rel.add_argument("--package", required=True)
    p_rel.add_argument("--version")

    p_create = sub.add_parser("create", help="crear proceso desde una release")
    p_create.add_argument("--name", required=True)
    p_create.add_argument("--release", required=True, help="paquete@version | paquete | release_id")
    p_create.add_argument("--timeout", type=int, default=0, help="segundos (0 = sin límite)")
    p_create.add_argument("--max-retries", type=int, default=0)
    p_create.add_argument("--auto-retry", action="store_true")
    p_create.add_argument("--assets", help="required_assets separados por coma")
    p_create.add_argument("--tags", help="tags separados por coma")
    p_create.add_argument("--description")

    p_active = sub.add_parser("active", help="activar/desactivar proceso")
    p_active.add_argument("process_id")
    grupo = p_active.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--on", action="store_true")
    grupo.add_argument("--off", action="store_true")

    p_setrel = sub.add_parser(
        "set-release", help="apuntar el proceso a otra release (promote/rollback; sesión)"
    )
    p_setrel.add_argument("process", help="UUID o nombre del proceso")
    p_setrel.add_argument("--release", required=True, help="paquete@version | paquete | release_id")

    args = parser.parse_args()

    if args.cmd == "list":
        result = nora_api.call(
            "GET", "/processes/list",
            params={"page": args.page, "limit": args.limit},
            session_path="/processes",
        )
        nora_api.emit(result)

    elif args.cmd == "releases":
        result = nora_api.call(
            "GET", "/releases/list",
            params={"package": args.package, "limit": 100},
            session_path="/releases",
        )
        releases = result["data"] if isinstance(result, dict) else result
        if args.version:
            releases = [r for r in releases if r["version"] == args.version]
        nora_api.emit(releases)

    elif args.cmd == "create":
        body = {
            "name": args.name,
            "release_id": resolve_release_id(args.release),
            "timeout_seconds": args.timeout,
            "max_retries": args.max_retries,
            "auto_retry": args.auto_retry,
        }
        if args.assets:
            body["required_assets"] = [a.strip() for a in args.assets.split(",") if a.strip()]
        if args.tags:
            body["tags"] = [t.strip() for t in args.tags.split(",") if t.strip()]
        if args.description:
            body["description"] = args.description
        process = nora_api.call("POST", "/processes/create", body=body, session_path="/processes")
        nora_api.eprint(f"Proceso '{args.name}' creado: {process['id']}")
        nora_api.emit(process)

    elif args.cmd == "active":
        process = nora_api.call_api_key(
            "PATCH", f"/processes/{nora_api.seg(args.process_id)}/active",
            body={"is_active": bool(args.on)},
        )
        nora_api.emit(process)

    elif args.cmd == "set-release":
        from nora_trigger import resolve_process_id

        process_id = resolve_process_id(args.process)
        release_id = resolve_release_id(args.release)
        process = nora_api.call_session(
            "PATCH", f"/processes/{nora_api.seg(process_id)}/active-release",
            body={"release_id": release_id},
        )
        nora_api.eprint(f"Proceso {process['name']} ahora apunta a la release {release_id}.")
        nora_api.emit(process)


if __name__ == "__main__":
    nora_api.run(main)
