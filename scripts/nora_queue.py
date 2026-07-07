#!/usr/bin/env python3
"""Gestiona colas de NORA: crear, encolar items, listar, estadísticas.

Uso:
    nora_queue.py create <nombre> [--description "..."] [--max-retries 3]
    nora_queue.py add <nombre> --data '{"factura": "F-001"}' \
        [--priority 1|3|5] [--reference F-001] [--deadline ISO] [--postpone ISO]
    nora_queue.py bulk <nombre> --file items.json [--priority 3]
    nora_queue.py list <nombre> [--status new|in_progress|pending_review|completed|failed|dead_letter] [--page 1] [--limit 20]
    nora_queue.py stats <nombre>

`bulk --file` espera un JSON con una lista de objetos (máx 1000 por llamada).
Scopes: queues:manage / queues:write / queues:read.
"""

import argparse
import json

import nora_api

STATUSES = ["new", "in_progress", "pending_review", "completed", "failed", "dead_letter"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_create = sub.add_parser("create", help="crear una cola")
    p_create.add_argument("nombre")
    p_create.add_argument("--description")
    p_create.add_argument("--max-retries", type=int, default=3,
                          help="reintentos de excepciones de sistema antes de dead_letter (0-10)")

    p_add = sub.add_parser("add", help="agregar un item")
    p_add.add_argument("nombre")
    p_add.add_argument("--data", required=True, help="payload del item como JSON")
    p_add.add_argument("--priority", type=int, choices=[1, 3, 5], default=3)
    p_add.add_argument("--reference", help="clave de idempotencia/trazabilidad")
    p_add.add_argument("--deadline", help="fecha límite ISO-8601")
    p_add.add_argument("--postpone", help="no procesar antes de (ISO-8601)")

    p_bulk = sub.add_parser("bulk", help="agregar items masivamente")
    p_bulk.add_argument("nombre")
    p_bulk.add_argument("--file", required=True, help="JSON con lista de objetos")
    p_bulk.add_argument("--priority", type=int, choices=[1, 3, 5], default=3)

    p_list = sub.add_parser("list", help="listar items")
    p_list.add_argument("nombre")
    p_list.add_argument("--status", choices=STATUSES)
    p_list.add_argument("--page", type=int, default=1)
    p_list.add_argument("--limit", type=int, default=20)

    p_stats = sub.add_parser("stats", help="conteo de items por estado")
    p_stats.add_argument("nombre")

    args = parser.parse_args()

    if args.cmd == "create":
        body = {"name": args.nombre, "max_retries": args.max_retries}
        if args.description:
            body["description"] = args.description
        queue = nora_api.call("POST", "/queues/create", body=body, session_path="/queues")
        nora_api.emit(queue)

    elif args.cmd == "add":
        body = {"data": json.loads(args.data), "priority": args.priority}
        for campo in ("reference", "deadline", "postpone"):
            valor = getattr(args, campo)
            if valor:
                body[campo] = valor
        item = nora_api.call_api_key("POST", f"/queues/by-name/{args.nombre}/items", body=body)
        nora_api.emit(item)

    elif args.cmd == "bulk":
        with open(args.file, encoding="utf-8") as f:
            items = json.load(f)
        if not isinstance(items, list):
            raise nora_api.NoraError(f"{args.file} debe contener una lista JSON.", 2)
        total_agregados = 0
        for i in range(0, len(items), 1000):
            lote = items[i : i + 1000]
            result = nora_api.call_api_key(
                "POST", f"/queues/by-name/{args.nombre}/items/bulk",
                body={"items": lote, "priority": args.priority},
            )
            total_agregados += result.get("added", len(lote))
            nora_api.eprint(f"Lote {i // 1000 + 1}: {result.get('added')} items.")
        nora_api.emit({"added": total_agregados})

    elif args.cmd == "list":
        params = {"page": args.page, "limit": args.limit}
        if args.status:
            params["status"] = args.status
        result = nora_api.call_api_key(
            "GET", f"/queues/by-name/{args.nombre}/items", params=params
        )
        nora_api.emit(result)

    elif args.cmd == "stats":
        stats = {}
        for status in STATUSES:
            result = nora_api.call_api_key(
                "GET", f"/queues/by-name/{args.nombre}/items",
                params={"page": 1, "limit": 1, "status": status},
            )
            stats[status] = (result.get("meta") or {}).get("total", 0)
        stats["total"] = sum(stats.values())
        nora_api.emit(stats)


if __name__ == "__main__":
    nora_api.run(main)
