# Migrar de UiPath a NORA

> Guía viva complementaria: https://docs.valisoftconsulting.com/migracion/desde-uipath/

Es una **reimplementación asistida en Python**, no una transpilación de XAML.
Lo que se preserva: el diseño del proceso (colas, transacciones, assets,
triggers, manejo de excepciones). Lo que se reescribe: la automatización en sí
(Playwright/requests/pandas en vez de actividades).

## Tabla de mapeo de conceptos

| UiPath | NORA | Notas |
| --- | --- | --- |
| Orchestrator | Robots Center (orquestador) | |
| Process/Package (.nupkg) | Package → Release (zip) | `nora package` + `release push` |
| Robot/Machine (unattended) | Machine + agente NORA | Mac/Windows |
| Job | Job | estados, prioridad, progreso |
| **REFramework** | template `robot-transactional` | fases con el mismo nombre |
| Orchestrator Queue | Queue | `nora_queue.py create` |
| QueueItem / Transaction | QueueItem | `reference` = Reference |
| SetTransactionStatus Success | `nora.complete(...)` | |
| **BusinessRuleException** | `BusinessError` → `fail_business` | terminal, NO reintenta |
| **ApplicationException** | excepción normal → `fail_system` | reintenta hasta max_retries |
| Auto-Retry de la cola | `max_retries` de la cola | |
| Abandoned (timeout item) | timeout del proceso + señal stop | |
| Asset (text/bool/int/credential) | Asset (`text`/`bool`/`integer`/`number`/`credential`/`secret`) | por entorno dev/staging/prod |
| Credential Asset / CyberArk | Asset `credential` (+ `vault` si aplica) | `nora.asset(name)` |
| Config.xlsx del REFramework | inputs de nora.json + assets | config por corrida → inputs; secretos/URLs → assets |
| In/Out Arguments | inputs/outputs de nora.json | validados por JSON Schema |
| Time Trigger | Schedule (cron + tz + feriados) | `nora_schedule.py create` |
| Queue Trigger | Trigger tipo cola | consola |
| Webhook/API start job | `POST /jobs/trigger` o trigger webhook | `nora_trigger_mgmt.py` |
| Orchestrator API | API pública X-API-Key | `api-reference.md` |
| Log Message | `nora.log(level, msg, data)` | |
| Report Status | `nora.update_progress()` | |
| Action Center (aprobar tareas) | review de cola (`send_for_review`/`wait_review`) o `ask_user` | Slack/Teams opcional |
| Selectores UI / UI Explorer | Playwright (web) / pyautogui, pywinauto (escritorio) | decidir según el target |
| Excel/DataTable activities | pandas / openpyxl | |
| HTTP Request activity | requests / httpx | |
| Mail activities | imaplib/smtplib o API del proveedor | o email trigger de NORA |
| Invoke Workflow | funciones/módulos Python | |
| Alertas de Orchestrator | canales de notificación (webhook/slack/teams/email) | `job_failed`, `machine_offline`... |

## Procedimiento

1. **Inventariar el proyecto origen**: abre `project.json` y los XAML
   principales (Main, GetTransactionData, Process). Extrae: colas usadas,
   assets consumidos, argumentos In/Out, la hoja Config.xlsx, triggers, y el
   flujo de negocio del Process.xaml en prosa.
2. **Llenar la tabla de mapeo** con los elementos reales del proyecto y
   presentarla al usuario para aprobación ANTES de escribir código.
3. **Recrear infraestructura**: colas (`nora_queue.py create`), assets
   (`nora_asset.py set`, empezando en `--env dev`), proceso y schedule al final.
4. **Implementar sobre `robot-transactional`**: la lógica del Process.xaml se
   convierte en `process_transaction()`; Init → `initialize()` (abrir apps,
   leer config); End → `end()`. Mantén los nombres de las transacciones
   (references) para comparar contra el bot original.
5. **Migrar datos en vuelo**: exporta los items pendientes de la cola de
   Orchestrator y cárgalos con `nora_queue.py bulk --reference-field <campo>`
   — cada item conserva su Reference original (idempotencia y trazabilidad en
   la consola).
6. **Validar en pirámide** (`testing-and-validation.md`) y correr **en paralelo**
   con el bot UiPath (en dev/staging o con muestra) comparando salidas antes de
   apagar el original.

## Sin equivalente directo — decidir y avisar

- **Selectores UiPath**: no se traducen. Web → Playwright (robusto, headless
  compatible con la resolución de sesión de NORA). Escritorio Windows →
  pywinauto/pyautogui.
- **Picture-in-Picture / attended complejo**: NORA cubre attended con
  `ask_user` y review de colas; interacción de escritorio compartido no.
- **Orchestrator Storage Buckets**: usar almacenamiento propio (S3, carpeta de
  red) referenciado por assets.
- **Insights**: el dashboard y analytics de NORA cubren lo básico; reportes
  avanzados vía API.
