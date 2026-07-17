# NORA Skill — RPA para Claude Code, Codex y Gemini

> **Skill oficial de NORA (Robots Center de Valisoft)** para desarrollar, migrar,
> operar y depurar **robots RPA en Python** desde agentes de IA. Compatible con
> **Claude Code, OpenAI Codex y Gemini CLI**.

![License: MIT](https://img.shields.io/badge/license-MIT-green)
![RPA](https://img.shields.io/badge/RPA-NORA-blue)
![Agents](https://img.shields.io/badge/agents-Claude%20Code%20·%20Codex%20·%20Gemini-purple)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

**NORA Skill** convierte a tu agente de IA en un ingeniero RPA experto en la
plataforma **NORA** (el orquestador de robots de **Valisoft Consulting**). Es la
forma más rápida de crear robots de automatización, migrar desde **UiPath** o
**Automation Anywhere**, y controlar el orquestador desde tu terminal.

Le da a tu agente la capacidad de:

- **Desarrollar robots NORA desde cero** con nivel profesional: manifiesto,
  argumentos tipados, colas transaccionales, assets, excepciones
  negocio/sistema, logging, progreso, attended. Templates para web
  (**Playwright**), escritorio Windows (**pywinauto**), dispatcher/performer y
  más, con **scaffolding** (`new_robot.py`) y diagnóstico de entorno
  (`doctor.py`).
- **Migrar automatizaciones existentes**: scripts Python sueltos
  (selenium/pandas/requests) y procesos de **UiPath** o **Automation
  Anywhere** (REFramework → patrón transaccional, Orchestrator/WLM queues →
  colas NORA, Credential Vault → assets).
- **Operar, gestionar y depurar el orquestador en vivo** vía API pública:
  lanzar/monitorear jobs, leer sus **logs**, crear
  colas/assets/procesos/schedules/triggers, reintentar dead_letter en lote,
  promote/rollback de releases, gestionar la **flota de agentes** y su
  auto-update, smoke tests end-to-end.
- **Auto-validar lo que genera**: pirámide de 6 niveles (estático → pytest →
  local → `nora dev run` → checklist → smoke e2e).

Docs de la plataforma: https://docs.valisoftconsulting.com

## Instalación

```bash
git clone https://github.com/valisoftconsulting/nora-skill.git
cd nora-skill
./install.sh --all          # Claude Code + Codex + Gemini (global)
# o por agente / por proyecto:
./install.sh --claude
./install.sh --codex --project ~/mi-proyecto
./install.sh --gemini
```

- **Claude Code**: symlink en `~/.claude/skills/nora` — el skill se activa
  solo cuando la conversación menciona NORA.
- **Codex / Gemini**: bloque puntero (idempotente, entre marcadores) en
  `AGENTS.md` / `GEMINI.md` que le indica al agente leer `SKILL.md`.

Actualizar: `git pull` (no muevas la carpeta: los punteros usan ruta absoluta).
Desinstalar: `./install.sh --uninstall`.

## Requisitos según lo que hagas

| Tarea | Necesitas |
| --- | --- |
| Generar/migrar código de robots | nada (templates + references autocontenidos) |
| Probar localmente con colas/assets reales | `pip install nora-sdk` + `nora login` |
| Publicar releases | rol **admin** en tu workspace NORA |
| Operar/gestionar por API | `NORA_API_KEY` (Settings → API Keys, plan Pro/Enterprise) |

```bash
export NORA_API_KEY=nora_ak_...       # nunca la pongas en flags ni la comitees
# opcional (default: producción de Valisoft):
export NORA_API_URL=https://nora-api.valisoftconsulting.com/api/v1
```

## Estructura

```
SKILL.md          punto de entrada del agente (flujos A–D + reglas duras)
references/       contratos verificados: SDK, API, colas, CLI, migraciones,
                  desktop-windows, files-and-excel, browser-patterns, checklist
scripts/          herramientas stdlib: new_robot, doctor, nora_list/trigger/job/
                  queue/asset/process/schedule/machine, nora_smoke, validate_manifest, self_check
templates/        robots base: minimal · transactional (REFramework) ·
                  dispatcher-performer · browser (Playwright) · desktop (pywinauto)
evals/            escenarios de prueba del skill (5 flujos)
```

## Mantenimiento del skill

- `python3 scripts/self_check.py` — detecta drift entre las references y el
  `nora-sdk` instalado (firmas + pin de versión), y copias desincronizadas de
  `nora_helpers.py`. Sale con error si el SDK no está instalado (no puede
  verificar = no es "OK").
- Las firmas de `references/sdk-reference.md` están fijadas a una versión del
  SDK (ver encabezado). Al actualizar el SDK: correr self_check, actualizar la
  reference y registrar en `CHANGELOG.md`.
- Si cambias `templates/nora_helpers.py`, re-copia a los cinco
  `templates/robot-*/` (self_check exige igualdad byte a byte).

## Licencia

MIT para este skill. NORA es un producto propietario de Valisoft Consulting.

---

### Sobre NORA y este skill

**NORA** es el **Robots Center** (orquestador RPA) de **Valisoft Consulting**:
permite desarrollar, desplegar, agendar y monitorear **robots de automatización
de procesos (RPA)** escritos en **Python**. Este **skill de NORA** para
**Claude Code**, **OpenAI Codex** y **Gemini CLI** automatiza todo el ciclo de
vida del robot: scaffolding, colas transaccionales, assets/credenciales, jobs,
procesos, schedules, triggers, releases y gestión de la flota de agentes.

**Palabras clave:** NORA, nora-skill, Valisoft, Robots Center, RPA, robot RPA
Python, automatización de procesos, orquestador RPA, nora-sdk, Claude Code skill,
Codex, Gemini CLI, migración UiPath a NORA, migración Automation Anywhere,
REFramework, Orchestrator queues, Playwright, pywinauto, SAP GUI, dispatcher
performer, colas transaccionales, dead letter, automatización Excel.

**Enlaces:** [Documentación de NORA](https://docs.valisoftconsulting.com) ·
[Valisoft Consulting](https://valisoftconsulting.com)
