#!/usr/bin/env python3
"""Crea triggers webhook entrantes de NORA y rota sus secrets.

Uso:
    nora_trigger_mgmt.py create --name "Desde ERP" --process <uuid|nombre> \
        [--machine <uuid>] [--description "..."]
    nora_trigger_mgmt.py rotate-secret <trigger_id>

IMPORTANTE: el webhook_secret se muestra UNA sola vez en la respuesta —
guárdalo de inmediato en tu gestor de secretos. El sistema externo dispara con:
    POST {NORA_API_URL}/triggers/inbound/{token}
    X-Webhook-Signature: sha256=<HMAC-SHA256(secret, body)>

Scope: triggers:manage (+ feature webhooks). Fallback: sesión de `nora login`.
"""

import argparse

import nora_api
from nora_trigger import resolve_process_id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_create = sub.add_parser("create", help="crear trigger webhook")
    p_create.add_argument("--name", required=True)
    p_create.add_argument("--process", required=True, help="UUID o nombre del proceso")
    p_create.add_argument("--machine", help="UUID de máquina (opcional)")
    p_create.add_argument("--description")

    p_rotate = sub.add_parser("rotate-secret", help="rotar el HMAC secret")
    p_rotate.add_argument("trigger_id")

    args = parser.parse_args()

    if args.cmd == "create":
        body = {"name": args.name, "process_id": resolve_process_id(args.process)}
        if args.machine:
            body["machine_id"] = args.machine
        if args.description:
            body["description"] = args.description
        trigger = nora_api.call("POST", "/triggers/create", body=body, session_path="/triggers")
        nora_api.eprint(
            "Trigger creado. GUARDA EL SECRET AHORA — no se puede volver a consultar."
        )
        nora_api.emit(trigger)

    elif args.cmd == "rotate-secret":
        result = nora_api.call(
            "POST", f"/triggers/{args.trigger_id}/rotate-secret",
            session_path=f"/triggers/{args.trigger_id}/regenerate-secret",
        )
        nora_api.eprint("Secret rotado. GUARDA EL NUEVO SECRET AHORA.")
        nora_api.emit(result)


if __name__ == "__main__":
    nora_api.run(main)
