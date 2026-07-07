#!/usr/bin/env python3
"""Smoke test e2e de un proceso NORA: dispara → sigue → verifica outputs.

Uso:
    nora_smoke.py --process <uuid|nombre> [--machine <uuid>] \
        [--input '{"mes": "2026-07"}'] \
        [--expect-output procesados=3 --expect-output resumen~="OK"] \
        [--timeout 900]

--expect-output acepta `clave=valor` (igualdad como texto) o `clave~=texto`
(contiene). Exit 0 si el job completa y las aserciones pasan; 1 si no.
Es el último paso de todo despliegue de robot.
Scopes: jobs:write + jobs:read.
"""

import argparse
import json
import sys

import nora_api
from nora_trigger import follow, resolve_process_id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--process", required=True, help="UUID o nombre del proceso")
    parser.add_argument("--machine", help="UUID de máquina (opcional: auto-asigna)")
    parser.add_argument("--input", help="input_data como JSON")
    parser.add_argument("--expect-output", action="append", default=[],
                        metavar="CLAVE=VALOR|CLAVE~=TEXTO",
                        help="aserción sobre output_data (repetible)")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    body = {"process_id": resolve_process_id(args.process), "priority": 3}
    if args.machine:
        body["machine_id"] = args.machine
    if args.input:
        body["input_data"] = json.loads(args.input)

    nora_api.eprint(f"[smoke] Disparando '{args.process}'...")
    job = nora_api.call("POST", "/jobs/trigger", body=body, session_path="/jobs")
    job = follow(job["id"], args.timeout)

    fallos: list[str] = []
    if job.get("status") != "completed":
        fallos.append(f"estado final '{job.get('status')}' (esperaba 'completed'); "
                      f"error: {job.get('error_message')}")

    outputs = job.get("output_data") or {}
    for expectativa in args.expect_output:
        if "~=" in expectativa:
            clave, _, esperado = expectativa.partition("~=")
            real = str(outputs.get(clave.strip(), ""))
            if esperado.strip() not in real:
                fallos.append(f"output '{clave.strip()}': '{real}' no contiene '{esperado.strip()}'")
        elif "=" in expectativa:
            clave, _, esperado = expectativa.partition("=")
            real = str(outputs.get(clave.strip(), ""))
            if real != esperado.strip():
                fallos.append(f"output '{clave.strip()}': '{real}' != '{esperado.strip()}'")
        else:
            raise nora_api.NoraError(f"Aserción inválida: '{expectativa}' (usa k=v o k~=texto).", 2)

    resultado = {
        "job_id": job.get("id"),
        "status": job.get("status"),
        "output_data": outputs,
        "assertions_failed": fallos,
        "ok": not fallos,
    }
    nora_api.emit(resultado)
    if fallos:
        for fallo in fallos:
            nora_api.eprint(f"[smoke] FALLO: {fallo}")
        sys.exit(1)
    nora_api.eprint("[smoke] OK — job completado y outputs verificados.")


if __name__ == "__main__":
    nora_api.run(main)
