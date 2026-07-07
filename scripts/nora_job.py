#!/usr/bin/env python3
"""Consulta, sigue, detiene, relanza o responde un job de NORA.

Uso:
    nora_job.py status <job_id> [--follow] [--timeout 600]
    nora_job.py stop <job_id>
    nora_job.py rerun <job_id> [--input '{"k": "v"}']
    nora_job.py respond <job_id> --value "Sí"

status/stop: API key (jobs:read / jobs:stop) con fallback a sesión.
rerun/respond: SOLO sesión de `nora login` (endpoints internos).
`respond` contesta un ask_user() pendiente de un job attended.
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

    p_rerun = sub.add_parser("rerun", help="relanzar el job (sesión nora login)")
    p_rerun.add_argument("job_id")
    p_rerun.add_argument("--input", help="input_data nuevo como JSON (opcional)")

    p_respond = sub.add_parser("respond", help="responder input pendiente de job attended (sesión)")
    p_respond.add_argument("job_id")
    p_respond.add_argument("--value", required=True, help="respuesta para el ask_user() pendiente")

    args = parser.parse_args()

    if args.cmd == "rerun":
        import json as json_mod

        body = None
        if args.input:
            body = {"input_data": json_mod.loads(args.input)}
        job = nora_api.call_session(
            "POST", f"/jobs/{nora_api.seg(args.job_id)}/rerun", body=body
        )
        nora_api.eprint(f"Job relanzado: {job.get('id')} (estado {job.get('status')}).")
        nora_api.emit(job)
        return

    if args.cmd == "respond":
        result = nora_api.call_session(
            "POST", f"/jobs/{nora_api.seg(args.job_id)}/submit-input",
            body={"value": args.value},
        )
        nora_api.emit(result)
        return

    if args.cmd == "stop":
        job = nora_api.call(
            "POST", f"/jobs/{nora_api.seg(args.job_id)}/stop",
            session_path=f"/jobs/{nora_api.seg(args.job_id)}/stop", session_method="PATCH",
        )
        nora_api.emit(job)
        return

    inicio = time.time()
    ultimo = ""
    while True:
        job = nora_api.call("GET", f"/jobs/{nora_api.seg(args.job_id)}", session_path=f"/jobs/{nora_api.seg(args.job_id)}")
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
