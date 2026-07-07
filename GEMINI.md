<!-- Wrapper para Gemini CLI. La fuente de verdad es SKILL.md. -->

# Skill NORA (robots RPA de Valisoft)

Este repositorio es un **skill** para desarrollar, migrar y operar robots RPA
en NORA (Robots Center). Cuando la tarea involucre NORA — robots Python,
`nora.json`, colas/queues, assets, jobs, procesos, schedules, migrar un script
Python o un proceso de UiPath/Automation Anywhere, o la API del orquestador —:

1. Lee `SKILL.md` (este directorio) y elige el flujo A–D que corresponda.
2. Carga las `references/` que ese flujo indique — solo bajo demanda, no todas.
3. Usa los `scripts/` (`python3 scripts/<x>.py --help`) para la API en vivo y
   los `templates/` como base de todo robot nuevo.

Reglas mínimas aunque no leas nada más:
- Cero credenciales hardcodeadas: van en Assets de NORA (`nora_asset.py set`).
- Excepciones de cola: dato inválido = `business` (terminal); fallo transitorio
  = `system` (la plataforma reintenta). Nunca reintentes manualmente.
- Valida antes de publicar: `scripts/validate_manifest.py`, pytest,
  `python main.py`, `nora dev run` — y solo entonces `nora package` +
  `nora release push` (rol admin).
- Credenciales de API solo por env vars (`NORA_API_KEY`); nunca en flags ni en
  la salida.
