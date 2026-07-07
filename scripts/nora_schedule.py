#!/usr/bin/env python3
"""Crea y gestiona programaciones (schedules cron) de NORA.

Uso:
    nora_schedule.py create --name "Diario 7am" --process <uuid|nombre> \
        --cron "0 7 * * 1-5" [--tz America/Lima] [--machine <uuid>] \
        [--skip-holidays] [--input '{"modo": "auto"}'] [--description "..."]
    nora_schedule.py active <schedule_id> --on|--off

Scope: schedules:manage. Fallback: sesión de `nora login` (solo create).
"""

import argparse
import json

import nora_api
from nora_trigger import resolve_process_id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_create = sub.add_parser("create", help="crear schedule")
    p_create.add_argument("--name", required=True)
    p_create.add_argument("--process", required=True, help="UUID o nombre del proceso")
    p_create.add_argument("--cron", required=True, help='expresión cron, ej. "0 7 * * 1-5"')
    p_create.add_argument("--tz", default="America/Lima")
    p_create.add_argument("--machine", help="UUID de máquina (opcional)")
    p_create.add_argument("--skip-holidays", action="store_true")
    p_create.add_argument("--input", help="input_data como JSON")
    p_create.add_argument("--description")

    p_active = sub.add_parser("active", help="habilitar/pausar schedule")
    p_active.add_argument("schedule_id")
    grupo = p_active.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--on", action="store_true")
    grupo.add_argument("--off", action="store_true")

    args = parser.parse_args()

    if args.cmd == "create":
        body = {
            "name": args.name,
            "process_id": resolve_process_id(args.process),
            "cron_expression": args.cron,
            "timezone": args.tz,
            "skip_holidays": args.skip_holidays,
        }
        if args.machine:
            body["machine_id"] = args.machine
        if args.input:
            body["input_data"] = json.loads(args.input)
        if args.description:
            body["description"] = args.description
        schedule = nora_api.call("POST", "/schedules/create", body=body, session_path="/schedules")
        nora_api.eprint(
            f"Schedule '{args.name}' creado: {schedule['id']} "
            f"(próxima corrida: {schedule.get('next_run_at')})"
        )
        nora_api.emit(schedule)

    elif args.cmd == "active":
        schedule = nora_api.call_api_key(
            "PATCH", f"/schedules/{args.schedule_id}/active",
            body={"is_enabled": bool(args.on)},
        )
        nora_api.emit(schedule)


if __name__ == "__main__":
    nora_api.run(main)
