---
name: nora
description: >
  Desarrolla, migra, opera y depura robots RPA en NORA (Robots Center de
  Valisoft). Úsalo cuando el usuario mencione: NORA, nora-sdk, nora.json,
  robots RPA en Python, robot web (Playwright/selenium) o de escritorio Windows
  (pywinauto/SAP GUI), automatizar Excel/CSV, migrar un script Python a robot,
  migrar desde UiPath o Automation Anywhere (REFramework, Orchestrator queues,
  Control Room, Credential Vault), colas/queues, assets, jobs, procesos,
  schedules, triggers, disparar o monitorear procesos en el orquestador,
  reintentar dead_letter, versión/auto-update del agente y la flota de
  máquinas, nora dev run, nora package, release push.
  Keywords: RPA, robot, orquestador, automatización, Valisoft, queue, asset,
  dispatcher, performer, attended, migration, orchestrator, Playwright,
  pywinauto, Excel, scaffolding, fleet.
license: MIT
metadata:
  version: "1.2.0"
  compatible-sdk: "nora-sdk >= 0.8"
  docs: https://docs.valisoftconsulting.com
---

# NORA — desarrollo, migración y operación de robots RPA

## Modelo mental (10 líneas)

NORA orquesta robots **Python** en máquinas Mac/Windows con agente instalado.
Un robot = proyecto Python + manifiesto `nora.json` (argumentos in/out
tipados). Se empaqueta (`nora package`) y publica como **Release** de un
**Package**; un **Process** apunta a la release con timeout/retries/assets
requeridos; cada ejecución es un **Job** en una **Machine**. Trabajo
transaccional va en **Queues** (items con estados, reintentos y excepción
`business` terminal vs `system` reintentable). Secretos/config en **Assets**
tipados por entorno (dev/staging/production). Disparo por **Schedule** (cron),
**Trigger** (webhook, cola, archivo o correo) o API. Todo lo operable desde fuera usa la
**API pública** con `X-API-Key` y scopes.

## Cómo usar este skill

Elige UN flujo (A–D) y carga SOLO las references que indica — no leas todo.
Los scripts se invocan como `python3 <skill>/scripts/<script>.py` (stdlib puro,
JSON por stdout). Credenciales SIEMPRE por env vars: `NORA_API_KEY`
(API pública) y opcional `NORA_API_URL`; o sesión de `nora login` como
fallback automático.

### A. Desarrollar un robot desde cero

Referencias: `references/robot-architecture.md` + `references/sdk-reference.md`
(+ `references/queues-and-exceptions.md` si hay cola; + `browser-patterns.md`,
`desktop-windows.md` o `files-and-excel.md` según el target).

1. `scripts/doctor.py` para confirmar el entorno (Python, SDK, sesión, API key,
   máquinas). Entrevista mínima: ¿qué hace? ¿cuántos items por corrida?
   ¿credenciales o URLs de sistemas? ¿web, escritorio o archivos? ¿aprobación
   humana? ¿cómo se dispara?
2. Elige template con la tabla de decisión de robot-architecture y créalo con
   `scripts/new_robot.py <nombre> --template <minimal|transactional|
   dispatcher-performer|browser|desktop> [--queue <cola>]`.
3. **Contrato primero**: completa `nora.json` (inputs/outputs con description) y
   valida con `scripts/validate_manifest.py` antes de codificar.
4. Implementa la lógica llamando SOLO a `nora_helpers.py` (nunca el SDK a pelo
   desde la lógica de negocio).
5. Infraestructura: cola (`scripts/nora_queue.py create`), assets
   (`scripts/nora_asset.py set ... --env dev` primero).
6. **Bucle de auto-validación** (obligatorio): recorre
   `references/testing-and-validation.md` niveles 1→6 — estático, pytest,
   `python main.py`, `nora dev run`, checklist, publicar + smoke e2e. No
   publiques con un nivel en rojo.

### B. Migrar un script Python existente

Referencia: `references/migration-python-script.md`.

1. Lee el script y produce el **inventario** (inputs, secretos, salidas,
   loops, excepts) — preséntalo al usuario ANTES de tocar código.
2. Mapea: hardcodes→inputs, credenciales→assets, prints→log,
   resultado→outputs; cola si >20 items o reintentos/auditoría por item.
3. Porta la lógica tal cual al template (se muda, no se reescribe) y clasifica
   cada except en business/system.
4. Sigue el flujo A desde el paso 5.

### C. Migrar desde UiPath / Automation Anywhere

Referencia: `references/migration-uipath.md` o
`references/migration-automation-anywhere.md` (+ guía viva de docs si hace
falta).

1. Inventaria el proyecto origen (XAML/Config.xlsx o bot/WLM/Credential Vault).
2. Llena la **tabla de mapeo** y preséntala al usuario para aprobación.
3. Recrea infraestructura (colas, assets) con los scripts; implementa sobre
   `robot-transactional` (fases = REFramework); migra items en vuelo con
   `nora_queue.py bulk`.
4. Flujo A pasos 5–6 + **corrida en paralelo** contra el bot original antes de
   apagarlo.

### D. Operar el orquestador (API en vivo)

Referencia: `references/api-reference.md` (tabla endpoint→scope→script).

1. Verifica el entorno con `scripts/doctor.py` (valida `NORA_API_KEY` y sus
   scopes reales, sesión, máquinas online). Si falta la key, di dónde generarla
   (Settings → API Keys, plan Pro/Enterprise) y qué scopes necesita — falla
   temprano, no a mitad.
2. Descubre con `scripts/nora_list.py machines|processes|queues|schedules|jobs|triggers`.
3. Opera con el script correspondiente; para jobs usa SIEMPRE `--wait` o
   `nora_job.py status --follow` — nunca dejes un job disparado sin reportar
   su desenlace.
4. Diagnóstico de fallos (runbook completo en api-reference): job →
   `nora_job.py status`/`logs [--archived]`; cola →
   `nora_queue.py list --status failed|dead_letter` y `stats`.
5. Remediación y despliegue sin UI: `nora_queue.py action retry <cola>
   --status dead_letter` (reintentos en lote tras arreglar la causa),
   `nora_process.py set-release` (promote/rollback de release),
   `nora_job.py rerun|respond` (relanzar / responder attended). Estos usan la
   sesión de `nora login` — la tabla de qué degrada está en api-reference.
6. Flota de agentes: `scripts/nora_machine.py create` (alta) y `fleet-version`
   (qué versión corre cada máquina; el auto-update es automático desde 0.8.0 —
   ver "Flota y versiones del agente" en api-reference).

## Reglas duras (siempre aplican)

- `nora.json` con inputs/outputs tipados (`text|integer|number|bool`) y
  `description` en cada input. Valídalo con `validate_manifest.py`.
- `requirements.txt` con versiones fijadas si hay deps — el agente NO instala
  nada no declarado.
- **Excepciones**: dato inválido = `business` (terminal, jamás se reintenta);
  fallo transitorio = `system` (la plataforma reintenta). Nunca marques
  `system` un error de validación de datos. Nunca reintentes manualmente.
- Loops largos: `should_stop()` cada iteración + `update_progress()` real.
- **Cero credenciales hardcodeadas**: todo por assets. Los valores
  secret/credential son write-only — no intentes leerlos por gestión.
- Nunca pases `NORA_API_KEY` como flag ni la imprimas; `nora_asset.py get`
  oculta valores salvo `--reveal` explícito.
- `nora release push` requiere rol admin y la API pública requiere plan
  Pro/Enterprise — avisa antes de intentar.
- Antes de publicar: bucle de auto-validación completo (niveles 1–6).

## Env vars

| Contexto | Variables |
| --- | --- |
| Robot en runtime (las inyecta el agente) | `NORA_JOB_ID`, `NORA_API_URL`, `NORA_EXEC_TOKEN`, `NORA_INPUT`, `NORA_ASSETS`, `NORA_DISPLAY_*` |
| Operación/gestión (scripts de este skill) | `NORA_API_KEY` (requerida salvo sesión), `NORA_API_URL` (opcional) |
| Dev local | las genera `nora dev run` / `nora dev env` |

## Docs vivas

Para precios, límites de plan, features nuevas o cualquier duda no cubierta:
`references/live-docs.md` (índice `/llms.txt`; en conflicto ganan las docs
vivas — avisa del desfase).
