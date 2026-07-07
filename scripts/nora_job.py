#!/usr/bin/env python3
"""Consulta, sigue o detiene un job de NORA.

Uso:
    nora_job.py status <job_id> [--follow] [--timeout 600]
    nora_job.py stop <job_id>

Scopes: jobs:read / jobs:stop. Fallback: sesión de `nora login`.
"""

import argparse
import sys
import time

import nora_api

TERMINAL = {"completed", "failed", "cancelled", "stopped"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_status = sub.add_parser("status", help="estado del job")
    p_status.add_argument("job_id")
    p_status.add_argument("--follow", action="store_true", help="poll hasta estado terminal")
    p_status.add_argument("--timeout", type=int, default=600)

    p_stop = sub.add_parser("stop", help="solicitar stop ordenado")
    p_stop.add_argument("job_id")

    args = parser.parse_args()

    if args.cmd == "stop":
        job = nora_api.call(
            "POST", f"/jobs/{args.job_id}/stop",
            session_path=f"/jobs/{args.job_id}/stop", session_method="PATCH",
        )
        nora_api.emit(job)
        return

    inicio = time.time()
    ultimo = ""
    while True:
        job = nora_api.call("GET", f"/jobs/{args.job_id}", session_path=f"/jobs/{args.job_id}")
        estado = job.get("status", "?")
        if not args.follow:
            nora_api.emit(job)
            return
        linea = f"{estado} {job.get('progress_percent') or 0}% {job.get('progress_message') or ''}".strip()
        if linea != ultimo:
            nora_api.eprint(f"[job {args.job_id[:8]}] {linea}")
            ultimo = linea
        if estado in TERMINAL:
            nora_api.emit(job)
            if estado != "completed":
                sys.exit(1)
            return
        if time.time() - inicio > args.timeout:
            raise nora_api.NoraError(f"Timeout de {args.timeout}s (job sigue '{estado}').", 1)
        time.sleep(5)


if __name__ == "__main__":
    nora_api.run(main)
