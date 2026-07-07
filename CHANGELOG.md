# Changelog

Formato: [SemVer](https://semver.org/lang/es/). Cada entrada registra contra
qué versión de `nora-sdk` y de la API pública se verificó el skill.

## 1.1.0 — 2026-07-07

Verificado contra **nora-sdk 0.7.10** (firmas idénticas a 0.7.9).
Correcciones de auditoría externa + capacidades nuevas:

- **Fix crítico CI/CD**: `nora login --password` es flag sin valor; el
  workflow de ejemplo ahora usa `printf | nora login --password` (getpass lee
  stdin sin TTY) y advierte que MFA rompe el login headless.
- **Bulk con metadatos por item** (requiere backend ≥ 2026-07-07): cada item
  puede ser un sobre `{data, reference, priority, deadline, postpone}`;
  `nora_queue.py bulk --reference-field` eleva un campo a reference.
- Scripts nuevos/ampliados: `nora_queue.py action retry|approve|reject|delete`
  (remediación en lote), `nora_process.py set-release` (promote/rollback),
  `nora_job.py rerun|respond` (attended), `nora_list.py
  queues|schedules|jobs|triggers`.
- Robustez: percent-encoding de nombres en URLs (`seg()`), Retry-After
  malformado tolerado, `--limit` capeado, install.sh valida `--project` y no
  arrasa un `skills/nora` que no sea symlink.
- Honestidad de docs: tabla exacta de qué subcomandos degradan a sesión;
  `wait_review` ahora devuelve `"timeout"` (no lo mapea a rejected);
  caveat de carrera review+performers paralelos; fails de cola loggean si no
  pueden marcar el item.
- Template nuevo `robot-browser` (Playwright con viewport de la sesión NORA) y
  tests en `robot-minimal`; párrafo de DAGs y canales de notificación.

## 1.0.0 — 2026-07-07

- Versión inicial.
- Verificado contra **nora-sdk 0.7.9** y la API pública de NORA con los
  endpoints de gestión (`queues:manage`, `assets:manage`, `processes:write`,
  `schedules:manage`, `triggers:manage`).
- Flujos: desarrollo desde cero (A), migración de scripts Python (B),
  migración UiPath/Automation Anywhere (C), operación por API (D).
- 3 templates de robot, 12 scripts de operación/gestión/validación,
  11 references, instalador multi-agente (Claude Code / Codex / Gemini).
