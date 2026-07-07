#!/usr/bin/env python3
"""Valida un nora.json localmente (sin red) — primer paso del bucle de calidad.

Uso:
    validate_manifest.py [ruta/al/robot | ruta/al/nora.json]   (default: .)

Valida: campos obligatorios, tipos de argumento permitidos, entry_point
existente y seguro, defaults coherentes con el tipo, semver. Advierte:
argumentos sin description, imports de terceros sin requirements.txt.
Exit 0 = válido · 1 = inválido · 2 = uso incorrecto.
"""

import ast
import json
import re
import sys
from pathlib import Path

VALID_TYPES = {"text", "string", "integer", "int", "number", "float", "bool", "boolean"}
_PY_CHECK = {
    "text": str, "string": str,
    "integer": int, "int": int,
    "number": (int, float), "float": (int, float),
    "bool": bool, "boolean": bool,
}
# Módulos stdlib comunes en robots (heurística para el warning de requirements)
_STDLIB_HINT = {
    "os", "sys", "re", "json", "csv", "time", "datetime", "pathlib", "logging",
    "math", "random", "itertools", "functools", "collections", "typing",
    "urllib", "http", "email", "smtplib", "imaplib", "sqlite3", "subprocess",
    "shutil", "tempfile", "zipfile", "io", "base64", "hashlib", "hmac",
    "uuid", "argparse", "dataclasses", "enum", "abc", "traceback", "unicodedata",
    "decimal", "string", "textwrap", "glob", "configparser", "queue", "threading",
    "concurrent", "asyncio", "socket", "ssl", "struct", "secrets", "warnings",
    "contextlib", "copy", "pickle", "statistics", "types", "xml", "html",
}
_LOCAL_HINT = {"nora_agent", "nora_helpers", "config", "transactions", "dispatcher", "performer"}


def error(msg: str) -> str:
    return f"  ✗ {msg}"


def warn(msg: str) -> str:
    return f"  ⚠ {msg}"


def third_party_imports(root: Path) -> set[str]:
    found: set[str] = set()
    for py in root.rglob("*.py"):
        if any(part in (".venv", "venv", "tests", "__pycache__") for part in py.parts):
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                found.add(node.module.split(".")[0])
    local_modules = {p.stem for p in root.glob("*.py")} | {p.name for p in root.iterdir() if p.is_dir()}
    return {
        name for name in found
        if name not in _STDLIB_HINT and name not in _LOCAL_HINT and name not in local_modules
    }


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    manifest_path = target if target.name == "nora.json" else target / "nora.json"
    root = manifest_path.parent

    if not manifest_path.exists():
        print(f"No existe {manifest_path}", file=sys.stderr)
        sys.exit(2)

    errores: list[str] = []
    avisos: list[str] = []

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(json.dumps({"valid": False, "errors": [f"JSON inválido: {e}"]}, ensure_ascii=False))
        sys.exit(1)

    # Campos base
    name = manifest.get("name")
    if not name or not isinstance(name, str):
        errores.append("Falta 'name' (string).")
    version = manifest.get("version", "")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(version)):
        errores.append(f"'version' debe ser semver X.Y.Z (actual: {version!r}).")

    entry = manifest.get("entry_point", "main.py")
    if ".." in entry or entry.startswith(("/", "\\")):
        errores.append(f"entry_point inseguro: {entry!r} (debe ser relativo, sin '..').")
    elif not (root / entry).exists():
        errores.append(f"entry_point '{entry}' no existe en {root}/.")

    # Argumentos
    for seccion in ("inputs", "outputs"):
        argumentos = manifest.get(seccion) or []
        if not isinstance(argumentos, list):
            errores.append(f"'{seccion}' debe ser una lista.")
            continue
        vistos: set[str] = set()
        for arg in argumentos:
            if not isinstance(arg, dict) or not arg.get("name"):
                errores.append(f"{seccion}: cada argumento necesita 'name'. ({arg!r})")
                continue
            arg_name = arg["name"]
            if arg_name in vistos:
                errores.append(f"{seccion}: argumento duplicado '{arg_name}'.")
            vistos.add(arg_name)
            arg_type = arg.get("type", "text")
            if arg_type not in VALID_TYPES:
                errores.append(
                    f"{seccion}.{arg_name}: tipo '{arg_type}' inválido "
                    f"(usa text|integer|number|bool)."
                )
            elif "default" in arg and arg["default"] is not None:
                expected = _PY_CHECK[arg_type]
                default = arg["default"]
                if isinstance(default, bool) and arg_type not in ("bool", "boolean"):
                    errores.append(f"{seccion}.{arg_name}: default booleano para tipo '{arg_type}'.")
                elif not isinstance(default, expected):
                    errores.append(
                        f"{seccion}.{arg_name}: default {default!r} no es de tipo '{arg_type}'."
                    )
            if seccion == "inputs" and not arg.get("description"):
                avisos.append(f"inputs.{arg_name}: sin 'description' (el operador la ve en el formulario).")

    # requirements.txt para dependencias de terceros
    third = third_party_imports(root)
    if third and not (root / "requirements.txt").exists():
        avisos.append(
            f"Imports de terceros sin requirements.txt: {', '.join(sorted(third))} "
            "(el agente NO instala nada que no esté declarado)."
        )

    print(json.dumps(
        {"valid": not errores, "manifest": str(manifest_path), "errors": errores, "warnings": avisos},
        ensure_ascii=False, indent=2,
    ))
    for e in errores:
        print(error(e), file=sys.stderr)
    for a in avisos:
        print(warn(a), file=sys.stderr)
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
