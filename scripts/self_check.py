#!/usr/bin/env python3
"""Detector de drift del skill: firmas del SDK, copias de nora_helpers y docs.

Uso:
    self_check.py [--offline]

Chequea:
1. Que las funciones del SDK documentadas en references/sdk-reference.md
   existan en el `nora_agent` instalado con la misma firma (si está instalado).
2. Que las copias de nora_helpers.py en los templates sean byte-idénticas a la
   fuente canónica templates/nora_helpers.py.
3. (Sin --offline) que las URLs de docs vivas respondan.

Exit 0 = sin drift · 1 = drift detectado · 2 = no se pudo chequear.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import re
import sys
import urllib.request
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
LIVE_URLS = [
    "https://docs.valisoftconsulting.com/llms.txt",
    "https://docs.valisoftconsulting.com/referencia/operar-con-ia/",
]


def check_sdk_signatures() -> list[str] | None:
    """Compara firmas Y versión del SDK instalado contra sdk-reference.md.

    Devuelve None si el SDK no está instalado (NO VERIFICADO ≠ sin drift).
    """
    problemas: list[str] = []
    try:
        import nora_agent
        from nora_agent import sdk
    except ImportError:
        return None

    reference = (SKILL_ROOT / "references" / "sdk-reference.md").read_text(encoding="utf-8")

    # Pin de versión: el sello "Verificado contra nora-sdk X.Y.Z" debe coincidir
    # con la versión instalada — si Valisoft publicó un SDK nuevo, esto lo grita
    # aunque las firmas no hayan cambiado.
    pin = re.search(r"nora-sdk (\d+\.\d+\.\d+)", reference)
    installed = getattr(nora_agent, "__version__", None)
    if pin and installed and pin.group(1) != installed:
        problemas.append(
            f"Versión del SDK instalado ({installed}) != sello de sdk-reference.md "
            f"({pin.group(1)}) — re-verificar firmas y actualizar el sello + CHANGELOG."
        )
    documentadas = set(re.findall(r"^### `(\w+)\(", reference, flags=re.MULTILINE))
    if not documentadas:
        problemas.append("sdk-reference.md no contiene firmas '### `funcion(...' — ¿formato cambiado?")
        return problemas

    for nombre in sorted(documentadas):
        funcion = getattr(sdk, nombre, None)
        if funcion is None:
            problemas.append(f"sdk.{nombre} documentada pero NO existe en el SDK instalado.")
            continue
        firma = f"{nombre}{inspect.signature(funcion)}"
        # La firma exacta debe aparecer en la reference (formato: ### `firma`)
        if f"### `{firma}`" not in reference:
            problemas.append(
                f"Firma cambiada: el SDK instalado tiene `{firma}` "
                f"pero sdk-reference.md documenta otra."
            )

    publicas = {
        n for n in dir(sdk)
        if not n.startswith("_") and callable(getattr(sdk, n)) and
        getattr(getattr(sdk, n), "__module__", "") == "nora_agent.sdk"
    }
    faltantes = publicas - documentadas
    if faltantes:
        problemas.append(f"Funciones del SDK sin documentar en sdk-reference.md: {sorted(faltantes)}")
    return problemas


def check_helpers_copies() -> list[str]:
    problemas: list[str] = []
    canonical = SKILL_ROOT / "templates" / "nora_helpers.py"
    canonical_hash = hashlib.sha256(canonical.read_bytes()).hexdigest()
    for copia in sorted(SKILL_ROOT.glob("templates/robot-*/nora_helpers.py")):
        if hashlib.sha256(copia.read_bytes()).hexdigest() != canonical_hash:
            problemas.append(
                f"{copia.relative_to(SKILL_ROOT)} difiere de templates/nora_helpers.py "
                "— re-copia la fuente canónica."
            )
    return problemas


def check_live_docs() -> list[str]:
    problemas: list[str] = []
    for url in LIVE_URLS:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "nora-skill/self-check"})
            with urllib.request.urlopen(request, timeout=15) as resp:
                if resp.status != 200:
                    problemas.append(f"{url} → HTTP {resp.status}")
        except Exception as e:
            problemas.append(f"{url} inaccesible: {e}")
    return problemas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--offline", action="store_true", help="no chequear URLs")
    args = parser.parse_args()

    sdk_result = check_sdk_signatures()
    problemas = (sdk_result or []) + check_helpers_copies()
    if not args.offline:
        problemas += check_live_docs()

    if problemas:
        print(f"\nDRIFT DETECTADO ({len(problemas)}):")
        for p in problemas:
            print(f"  ✗ {p}")
        print("\nActualiza las references/templates y registra el cambio en CHANGELOG.md.")
        sys.exit(1)
    if sdk_result is None:
        print(
            "NO VERIFICADO: nora-sdk no está instalado — no puedo comparar firmas.\n"
            "Instálalo (pip install nora-sdk) o corre con PYTHONPATH=<repo>/sdk."
        )
        sys.exit(2)
    print("OK — sin drift: SDK, copias de nora_helpers y docs en orden.")


if __name__ == "__main__":
    main()
