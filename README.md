# nora-skill

Skill oficial de **NORA** (Robots Center de Valisoft) para agentes de IA:
**Claude Code, OpenAI Codex y Gemini CLI**. Le da a tu agente la capacidad de:

- **Desarrollar robots NORA desde cero** con nivel profesional: manifiesto,
  argumentos tipados, colas transaccionales, assets, excepciones
  negocio/sistema, logging, progreso, attended.
- **Migrar automatizaciones existentes**: scripts Python sueltos
  (selenium/pandas/requests) y procesos de **UiPath** o **Automation
  Anywhere** (REFramework → patrón transaccional, Orchestrator/WLM queues →
  colas NORA, Credential Vault → assets).
- **Operar y gestionar el orquestador en vivo** vía API pública: lanzar y
  monitorear jobs, crear colas/assets/procesos/schedules/triggers, smoke tests
  end-to-end.
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
references/       contratos verificados: SDK, API, colas, CLI, migraciones, checklist
scripts/          herramientas stdlib contra la API (nora_list, nora_trigger, nora_queue, ...)
templates/        robots base: minimal · transactional (REFramework) · dispatcher-performer
evals/            escenarios de prueba del skill
```

## Mantenimiento del skill

- `python3 scripts/self_check.py` — detecta drift entre las references y el
  `nora-sdk` instalado, y copias desincronizadas de `nora_helpers.py`.
- Las firmas de `references/sdk-reference.md` están fijadas a una versión del
  SDK (ver encabezado). Al actualizar el SDK: correr self_check, actualizar la
  reference y registrar en `CHANGELOG.md`.
- Si cambias `templates/nora_helpers.py`, re-copia a los tres
  `templates/robot-*/` (self_check exige igualdad byte a byte).

## Licencia

MIT para este skill. NORA es un producto propietario de Valisoft Consulting.
