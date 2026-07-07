#!/usr/bin/env python3
"""Lee, crea o actualiza assets de NORA (config/credenciales cifradas).

Uso:
    nora_asset.py get <nombre> [--env production] [--reveal]
    nora_asset.py set <nombre> --type text|credential|secret|integer|number|bool \
        [--env production] [--value "..." | --value-stdin] [--username u] \
        [--description "..."]

`get` oculta el valor salvo --reveal (explícito, para no dejar secretos en
transcripts). `set` crea el asset; si ya existe (409) actualiza su valor por
nombre. Prefiere --value-stdin para no dejar el secreto en el historial.
Scopes: assets:read / assets:manage.
"""

import argparse
import sys

import nora_api


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_get = sub.add_parser("get", help="leer un asset por nombre")
    p_get.add_argument("nombre")
    p_get.add_argument("--env", default="production", choices=["dev", "staging", "production"])
    p_get.add_argument("--reveal", action="store_true", help="mostrar el valor descifrado")

    p_set = sub.add_parser("set", help="crear o actualizar un asset")
    p_set.add_argument("nombre")
    p_set.add_argument("--type", default="text",
                       choices=["text", "credential", "secret", "integer", "number", "bool"])
    p_set.add_argument("--env", default="production", choices=["dev", "staging", "production"])
    p_set.add_argument("--value", help="valor (queda en el historial de shell — mejor --value-stdin)")
    p_set.add_argument("--value-stdin", action="store_true", help="leer el valor desde stdin")
    p_set.add_argument("--username", help="requerido para type=credential")
    p_set.add_argument("--description")

    args = parser.parse_args()

    if args.cmd == "get":
        data = nora_api.call_api_key(
            "GET", f"/assets/by-name/{nora_api.seg(args.nombre)}", params={"environment": args.env}
        )
        if not args.reveal:
            data = {k: ("***" if k in ("value", "username") else v) for k, v in data.items()}
            nora_api.eprint("Valor oculto — usa --reveal para mostrarlo.")
        nora_api.emit(data)
        return

    if args.value_stdin:
        value = sys.stdin.read().rstrip("\n")
    elif args.value is not None:
        value = args.value
    else:
        raise nora_api.NoraError("Falta el valor: usa --value o --value-stdin.", 2)
    if args.type == "credential" and not args.username:
        raise nora_api.NoraError("type=credential requiere --username.", 2)

    body = {
        "name": args.nombre,
        "type": args.type,
        "value": value,
        "environment": args.env,
    }
    if args.username:
        body["username"] = args.username
    if args.description:
        body["description"] = args.description

    try:
        asset = nora_api.call("POST", "/assets/create", body=body, session_path="/assets")
        nora_api.eprint(f"Asset '{args.nombre}' creado en {args.env}.")
    except nora_api.NoraError as e:
        if not str(e).startswith("HTTP 409"):
            raise
        update = {"value": value}
        if args.username:
            update["username"] = args.username
        if args.description:
            update["description"] = args.description
        asset = nora_api.call_api_key(
            "PUT", f"/assets/by-name/{nora_api.seg(args.nombre)}",
            body=update, params={"environment": args.env},
        )
        nora_api.eprint(f"Asset '{args.nombre}' ya existía — valor actualizado.")
    nora_api.emit(asset)


if __name__ == "__main__":
    nora_api.run(main)
