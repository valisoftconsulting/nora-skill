#!/usr/bin/env python3
"""Lista máquinas o procesos del orquestador NORA.

Uso:
    nora_list.py machines [--page 1] [--limit 50]
    nora_list.py processes [--page 1] [--limit 50]

Scopes: machines:read / processes:read. Fallback: sesión de `nora login`.
"""

import argparse

import nora_api


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("recurso", choices=["machines", "processes"])
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    params = {"page": args.page, "limit": args.limit}
    if args.recurso == "machines":
        result = nora_api.call("GET", "/machines/list", params=params, session_path="/machines")
    else:
        result = nora_api.call("GET", "/processes/list", params=params, session_path="/processes")
    nora_api.emit(result)


if __name__ == "__main__":
    nora_api.run(main)
