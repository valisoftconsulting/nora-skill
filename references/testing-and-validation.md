# Pirámide de validación del robot

Después de generar o migrar un robot, recorre TODOS los niveles en orden y
**no publiques con un nivel en rojo**. Lee la salida de cada paso, corrige y
repite.

## Nivel 1 — Estático (sin red, segundos)

```bash
python3 <skill>/scripts/validate_manifest.py .
python3 -m py_compile main.py $(ls *.py)
```

Manifiesto válido (tipos, defaults, entry_point) + sintaxis. `validate_manifest`
también avisa si hay imports de terceros sin `requirements.txt` — el agente NO
instala nada no declarado.

## Nivel 2 — Tests unitarios (sin plataforma)

```bash
python -m pytest tests/ -q
```

La lógica de negocio (`transactions.py` / `process_item`) se prueba con datos
en duro y un fake de `nora_helpers` — los templates traen ejemplos. Cubre al
menos: caso feliz, un dato inválido (debe lanzar `BusinessError`), un caso
límite del dominio.

## Nivel 3 — Ejecución local degradada (sin credenciales)

```bash
python main.py
```

`nora_helpers` degrada: logs a consola, cola vacía, assets None. El robot debe
terminar limpio (sin traceback) también en este modo — así detectas
`NoneType` sin manejar y dependencias de plataforma escondidas en la lógica.

## Nivel 4 — Ejecución local real (`nora dev run`)

```bash
nora dev run main.py --input '{"mes": "2026-07"}' --assets CRED1 -e dev
```

Corre EN TU MÁQUINA con token dev contra el orquestador real (colas y assets
del entorno dev/staging). Prepara antes:
- Cola de pruebas: `nora_queue.py create mi-cola-dev` + `bulk` con 2-3 items.
- Assets de dev: `nora_asset.py set CRED1 --type credential --env dev ...`.

Verifica: los items quedaron `completed`/`failed` como esperabas
(`nora_queue.py list mi-cola-dev --status completed`), los outputs se
imprimieron, el log cuenta la historia.

Para depurar con breakpoints: `nora dev env --write .env` + envFile en el IDE.

## Nivel 5 — Checklist de calidad

Recorre `quality-checklist.md` ítem por ítem y reporta el resultado al usuario.

## Nivel 6 — Publicar y smoke e2e

```bash
nora package && nora release push
python3 <skill>/scripts/nora_process.py create --name "..." --release mi-robot  # si no existe
python3 <skill>/scripts/nora_smoke.py --process "..." \
  --input '{...}' --expect-output procesados=3 --timeout 900
```

`nora_smoke.py` dispara el job en una máquina conectada, sigue el progreso en
stderr y verifica estado `completed` + outputs esperados. Exit 0 = despliegue
verificado. Si no hay máquina online, `nora_list.py machines` para
diagnosticar.

## Matriz rápida

| Nivel | Necesita | Detecta |
| --- | --- | --- |
| 1 estático | nada | manifiesto/sintaxis rotos |
| 2 pytest | nada | lógica de negocio incorrecta |
| 3 python main.py | nada | dependencias de plataforma mal aisladas |
| 4 dev run | `nora login` | integración real: colas, assets, args |
| 5 checklist | — | secretos, retries, stop, progreso |
| 6 smoke e2e | API key + máquina | despliegue completo y outputs |
