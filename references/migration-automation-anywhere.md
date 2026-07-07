# Migrar de Automation Anywhere (A360) a NORA

> Guía viva complementaria: https://docs.valisoftconsulting.com/migracion/desde-automation-anywhere/

Igual que con UiPath: **reimplementación asistida en Python** preservando el
diseño (colas WLM, credenciales, triggers), reescribiendo la automatización.

## Tabla de mapeo de conceptos

| Automation Anywhere | NORA | Notas |
| --- | --- | --- |
| Control Room | Robots Center (orquestador) | |
| Bot (.atmx / flujo A360) | Robot Python (Package → Release) | |
| Bot Runner (unattended) | Machine + agente NORA | |
| Bot Agent | Agente NORA | Mac/Windows |
| Deployment / Run bot | Job | |
| **WLM (Workload Management) Queue** | Queue | `nora_queue.py create` |
| Work Item | QueueItem | `reference` = clave del work item |
| Work Item status (On Hold/Failed) | estados de QueueItem | pending_review / failed |
| WLM automation priority | `priority` del item (1/3/5) | |
| **Credential Vault** | Assets `credential`/`secret` | por entorno; write-only |
| Locker / credential attribute | asset por atributo o JSON en `secret` | 1 credencial = 1 asset |
| Global Values | Assets `text`/`integer`/`bool` | |
| Bot input/output variables | inputs/outputs de nora.json | |
| Schedule | Schedule (cron + tz + feriados) | `nora_schedule.py create` |
| API Task / Control Room API | API pública X-API-Key | `api-reference.md` |
| Trigger (hotkey/file/email) | Trigger de NORA (webhook/file watcher/email) | file/email se configuran en consola |
| MetaBot / paquete reutilizable | módulo Python compartido | repo pip interno si se comparte |
| Error Handler (Try/Catch blocks) | try/except + business/system | árbol en `queues-and-exceptions.md` |
| AARI (human in the loop) | review de cola / `ask_user` | |
| Audit Log | Audit log de NORA | |
| Bot Insight | dashboard + analytics de NORA | |
| IQ Bot / Document Automation | OCR/parsing en Python (pytesseract, LLM...) | rediseño |
| Recorder / packages de acciones | Playwright / pywinauto / pandas / requests | según target |

## Procedimiento

1. **Inventariar**: exporta/abre el bot en A360 y lista: work item template de
   la cola WLM, lockers/credenciales usadas, variables de entrada/salida,
   schedules y triggers, sub-bots invocados, y el flujo principal en prosa.
2. **Llenar la tabla de mapeo** con los elementos reales y presentarla al
   usuario para aprobación antes de codificar.
3. **Recrear infraestructura**: colas, assets (dev primero), luego proceso.
4. **Implementar sobre `robot-transactional`** (WLM ≈ cola transaccional):
   el flujo del bot → `process_transaction()`; sub-bots → funciones/módulos.
5. **Migrar work items pendientes**: exportar de WLM → `nora_queue.py bulk`.
6. **Validar en pirámide** y corrida en paralelo antes de apagar el bot A360.

## Diferencias a explicar al usuario

- A360 es low-code visual; NORA es Python: el equipo gana versionado git,
  tests y libertad de librerías, pero necesita mantener código.
- El Credential Vault de A360 permite leer credenciales desde la UI con
  permisos; en NORA los valores `secret`/`credential` son write-only — solo el
  robot en runtime los lee.
- Los triggers de dispositivo (hotkey) no tienen equivalente unattended: se
  reemplazan por webhook/schedule/file-watcher.
