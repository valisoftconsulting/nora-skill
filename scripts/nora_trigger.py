#!/usr/bin/env python3
"""Dispara un job en NORA (y opcionalmente espera el resultado).

Uso:
    nora_trigger.py --process <uuid|nombre> [--machine <uuid>] \
        [--input '{"mes": "2026-07"}' | --input-file inputs.json] \
        [--priority 1|3|5] [--wait] [--timeout 600]

Sin --machine el orquestador auto-asigna (solo vía API key). Con --wait hace
polling hasta estado terminal e imprime el job completo con outputs.
Scopes: jobs:write (+ jobs:read para --wait).
"""

import argparse
import json
import sys
import time
import uuid as uuid_mod

import nora_api

TERMINAL = {"completed", "failed", "cancelled", "stopped"}


def resolve_process_id(value: str) -> str:
    """Acepta UUID directo o nombre de proceso (busca en /processes/list)."""
    try:
        return str(uuid_mod.UUID(value))
    except ValueError:
        pass
    page = 1
    while True:
        result = nora_api.call(
            "GET", "/processes/list",
            params={"page": page, "limit": 100},
            session_path="/processes",
        )
        procesos = result["data"] if isinstance(result, dict) else result
        for p in procesos:
            if p["name"] == value:
                return p["id"]
        meta = result.get("meta") if isinstance(result, dict) else None
        if not meta or page >= meta.get("pages", 1):
            break
        page += 1
    raise nora_api.NoraError(f"Proceso '{value}' no encontrado.", 1)


def get_job(job_id: str) -> dict:
    return nora_api.call("GET", f"/jobs/{job_id}", session_path=f"/jobs/{job_id}")


def follow(job_id: str, timeout: int) -> dict:
    inicio = time.time()
    ultimo = ""
    while True:
        job = get_job(job_id)
        estado = job.get("status", "?")
        linea = f"{estado} {job.get('progress_percent') or 0}% {job.get('progress_message') or ''}".strip()
        if linea != ultimo:
            nora_api.eprint(f"[job {job_id[:8]}] {linea}")
            ultimo = linea
        if estado in TERMINAL:
            return job
        if time.time() - inicio > timeout:
            raise nora_api.NoraError(
                f"Timeout de {timeout}s esperando el job {job_id} (sigue '{estado}').", 1
            )
        time.sleep(5)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--process", required=True, help="UUID o nombre del proceso")
    parser.add_argument("--machine", help="UUID de máquina (opcional: auto-asigna)")
    parser.add_argument("--input", help="input_data como JSON inline")
    parser.add_argument("--input-file", help="ruta a un JSON con input_data")
    parser.add_argument("--priority", type=int, choices=[1, 3, 5], default=3)
    parser.add_argument("--wait", action="store_true", help="esperar estado terminal")
    parser.add_argument("--timeout", type=int, default=600, help="segundos máximos con --wait")
    args = parser.parse_args()

    input_data = None
    if args.input and args.input_file:
        raise nora_api.NoraError("Usa --input O --input-file, no ambos.", 2)
    if args.input:
        input_data = json.loads(args.input)
    elif args.input_file:
        with open(args.input_file, encoding="utf-8") as f:
            input_data = json.load(f)

    process_id = resolve_process_id(args.process)
    body = {"process_id": process_id, "priority": args.priority}
    if args.machine:
        body["machine_id"] = args.machine
    if input_data is not None:
        body["input_data"] = input_data

    job = nora_api.call("POST", "/jobs/trigger", body=body, session_path="/jobs")
    nora_api.eprint(f"Job creado: {job['id']} (estado {job.get('status')}).")

    if args.wait:
        job = follow(job["id"], args.timeout)
        nora_api.emit(job)
        if job.get("status") != "completed":
            nora_api.eprint(f"El job terminó en '{job.get('status')}': {job.get('error_message')}")
            sys.exit(1)
    else:
        nora_api.emit(job)


if __name__ == "__main__":
    nora_api.run(main)
