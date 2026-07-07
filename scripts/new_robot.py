#!/usr/bin/env python3
"""Scaffolding: crea un robot NORA nuevo desde un template del skill.

Uso:
    new_robot.py <nombre> --template minimal|transactional|dispatcher-performer|browser|desktop \
        [--queue mi-cola] [--dest .]

Copia el template, renombra el `name` en nora.json, ajusta el nombre de la
cola en config.py (si aplica) y deja el proyecto listo para el paso 1 del
bucle de validación (`validate_manifest.py`). Sin red.
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = {
    "minimal": "robot-minimal",
    "transactional": "robot-transactional",
    "dispatcher-performer": "robot-dispatcher-performer",
    "browser": "robot-browser",
    "desktop": "robot-desktop",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("nombre", help="nombre del robot (kebab-case, ej. registro-facturas)")
    parser.add_argument("--template", required=True, choices=sorted(TEMPLATES))
    parser.add_argument("--queue", help="nombre de la cola (templates con cola)")
    parser.add_argument("--dest", default=".", help="directorio padre (default: .)")
    args = parser.parse_args()

    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", args.nombre):
        print("El nombre debe ser kebab-case: minúsculas, números y guiones.", file=sys.stderr)
        sys.exit(2)

    src = SKILL_ROOT / "templates" / TEMPLATES[args.template]
    dest = Path(args.dest).resolve() / args.nombre
    if dest.exists():
        print(f"Ya existe {dest} — elige otro nombre o borra la carpeta.", file=sys.stderr)
        sys.exit(2)

    shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    # nora.json: nombre del robot
    manifest_path = dest / "nora.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["name"] = args.nombre
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # config.py: nombre de la cola
    config_path = dest / "config.py"
    if config_path.exists() and args.queue:
        s = config_path.read_text(encoding="utf-8")
        s = re.sub(r'QUEUE = "[^"]*"', f'QUEUE = "{args.queue}"', s)
        config_path.write_text(s, encoding="utf-8")
    elif args.queue and not config_path.exists():
        print(f"Aviso: el template '{args.template}' no usa cola — --queue ignorado.", file=sys.stderr)

    print(json.dumps({
        "robot": args.nombre,
        "template": args.template,
        "path": str(dest),
        "queue": args.queue,
        "next_steps": [
            f"cd {dest}",
            "editar nora.json (inputs/outputs con description)",
            f"python3 {SKILL_ROOT}/scripts/validate_manifest.py .",
            "implementar la lógica (solo via nora_helpers)",
            "python -m pytest tests/ -q && python main.py",
        ],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
