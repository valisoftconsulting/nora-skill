---
name: nora
description: >
  Desarrolla, migra y opera robots RPA en NORA (Robots Center de Valisoft).
  Úsalo cuando el usuario mencione: NORA, nora-sdk, nora.json, robots RPA en
  Python, migrar un script Python a robot, migrar desde UiPath o Automation
  Anywhere (REFramework, Orchestrator queues, Control Room, Credential Vault),
  colas/queues, assets, jobs, procesos, schedules, disparar o monitorear
  procesos en el orquestador, nora dev run, nora package, release push.
  Keywords: RPA, robot, orquestador, automatización, Valisoft, queue, asset,
  dispatcher, performer, attended, migration, orchestrator.
license: MIT
metadata:
  version: "1.0.0"
  compatible-sdk: "nora-sdk >= 0.7"
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
**Trigger** (webhook/cola/archivo) o API. Todo lo operable desde fuera usa la
**API pública** con `X-API-Key` y scopes.

## Cómo usar este skill

Elige UN flujo (A–D) y carga SOLO las references que indica — no leas todo.
Los scripts se invocan como `python3 <skill>/scripts/<script>.py` (stdlib puro,
JSON por stdout). Credenciales SIEMPRE por env vars: `NORA_API_KEY`
(API pública) y opcional `NORA_API_URL`; o sesión de `nora login` como
fallback automático.

### A. Desarrollar un robot desde cero

Referencias: `references/robot-architecture.md` + `references/sdk-reference.md`
(+ `references/queues-and-exceptions.md` si hay cola).

1. Entrevista mínima: ¿qué hace? ¿cuántos items por corrida? ¿credenciales o
   URLs de sistemas? ¿necesita aprobación humana? ¿cómo se dispara?
2. Elige template con la tabla de decisión de robot-architecture y cópialo de
   `templates/` (minimal | transactional | dispatcher-performer).
3. **Contrato primero**: escribe `nora.json` y valida con
   `scripts/validate_manifest.py` antes de codificar.
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

1. Verifica `NORA_API_KEY` (o sesión `nora login`). Si falta, di dónde
   generarla (Settings → API Keys, plan Pro/Enterprise) y qué scopes necesita
   la operación — falla temprano, no a mitad.
2. Descubre con `scripts/nora_list.py machines|processes`.
3. Opera con el script correspondiente; para jobs usa SIEMPRE `--wait` o
   `nora_job.py status --follow` — nunca dejes un job disparado sin reportar
   su desenlace.
4. Diagnóstico de fallos: job → `error_message`; cola →
   `nora_queue.py list --status failed|dead_letter` y stats.

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
