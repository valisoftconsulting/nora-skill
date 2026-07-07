# API pública de NORA (X-API-Key)

> Base: `https://nora-api.valisoftconsulting.com/api/v1` (override: `NORA_API_URL`).
> Referencia OpenAPI viva: https://docs.valisoftconsulting.com/api/referencia/

## Autenticación

- Header `X-API-Key: nora_ak_...` en toda petición.
- Las keys se crean en **Settings → API Keys** (planes Pro/Enterprise) con
  **scopes** explícitos, opcionalmente IPs permitidas, entornos permitidos
  (para lectura de assets) y expiración. La key completa se muestra UNA vez.
- Validación **fail-closed**: sin el scope exacto → 403. Key revocada/expirada
  → 401.

## Envelope

Toda respuesta: `{"success": true, "data": ...}`. Los listados agregan
`"meta": {"page", "limit", "total", "pages"}`. Los scripts del skill ya
desenvuelven esto.

## Endpoints, scopes y scripts

| Endpoint | Método | Scope | Límite/min | Script del skill |
| --- | --- | --- | --- | --- |
| `/machines/list` | GET | `machines:read` | 60 | `nora_list.py machines` |
| `/processes/list` | GET | `processes:read` | 60 | `nora_list.py processes` |
| `/processes/create` | POST | `processes:write` | 10 | `nora_process.py create` |
| `/processes/{id}/active` | PATCH | `processes:write` | 30 | `nora_process.py active` |
| `/releases/list?package=` | GET | `processes:read` | 60 | `nora_process.py releases` |
| `/jobs/trigger` | POST | `jobs:write` | 30 | `nora_trigger.py` |
| `/jobs/{id}` | GET | `jobs:read` | 60 | `nora_job.py status` |
| `/jobs/{id}/stop` | POST | `jobs:stop` | 30 | `nora_job.py stop` |
| `/assets/by-name/{n}` | GET | `assets:read` | 30 | `nora_asset.py get` |
| `/assets/create` | POST | `assets:manage` | 10 | `nora_asset.py set` |
| `/assets/by-name/{n}` | PUT | `assets:manage` | 10 | `nora_asset.py set` (si existe) |
| `/queues/create` | POST | `queues:manage` | 10 | `nora_queue.py create` |
| `/queues/by-name/{n}/items` | POST | `queues:write` | 60 | `nora_queue.py add` |
| `/queues/by-name/{n}/items` | GET | `queues:read` | 60 | `nora_queue.py list` / `stats` |
| `/queues/by-name/{n}/items/bulk` | POST | `queues:write` | 20 | `nora_queue.py bulk` (soporta sobre por item, ver abajo) |
| `/schedules/create` | POST | `schedules:manage` | 10 | `nora_schedule.py create` |
| `/schedules/{id}/active` | PATCH | `schedules:manage` | 30 | `nora_schedule.py active` |
| `/triggers/create` | POST | `triggers:manage` | 10 | `nora_trigger_mgmt.py create` |
| `/triggers/{id}/rotate-secret` | POST | `triggers:manage` | 10 | `nora_trigger_mgmt.py rotate-secret` |
| `/webhooks/trigger/{process_id}` | POST | (feature webhooks) | 60 | — (para sistemas externos) |

Detalles de payloads: docs vivas → `api/gestion`, `api/disparar-jobs`,
`api/colas`, `api/assets`.

## Bulk con metadatos por item (sobre)

Cada elemento de `items` en el bulk puede ser el data plano del item, **o un
sobre** para asignar metadatos por item:

```json
{
  "items": [
    { "cliente": "ACME" },
    { "data": {"cliente": "GLOBEX"}, "reference": "OC-9", "priority": 5,
      "deadline": "2026-12-31T23:59:00Z" }
  ],
  "priority": 3
}
```

- `reference` = clave de idempotencia/trazabilidad, visible en la consola.
- `priority` del request es el default para items sin priority propio.
- Si tu data legítimamente tiene una clave `data` de tipo dict al tope,
  envuélvela: `{"data": {"data": {...}}}`.
- `nora_queue.py bulk --reference-field id` eleva un campo a reference
  automáticamente.

## Reglas para operar

- `POST /jobs/trigger`: `machine_id` es opcional (auto-asigna). `input_data` se
  valida contra el `input_schema` del proceso → 422 con detalle si no cumple.
- **Nunca dispares un job sin reportar su desenlace**: usa `--wait` o
  `nora_job.py status --follow`.
- 429 → backoff exponencial (los scripts ya lo hacen, respetando Retry-After).
- Assets `secret`/`credential` son de escritura-solamente en gestión: crear y
  rotar sí; leer el valor solo con `assets:read` (runtime). `nora_asset.py get`
  oculta el valor salvo `--reveal`.

## Errores

| Código | Causa típica | Acción |
| --- | --- | --- |
| 401 | key ausente/revocada/expirada | revisar `NORA_API_KEY` |
| 403 | scope faltante (fail-closed) o feature fuera de plan | pedir key con el scope; plan Pro+ |
| 404 | nombre/UUID inexistente en el workspace | `nora_list.py` para descubrir |
| 409 | cola/asset ya existe | usar el existente o actualizar |
| 422 | input_data no cumple el schema; cron inválido | corregir payload |
| 429 | rate limit | backoff y reintentar |

## Runbook: corrida fallida (de síntoma a remedio)

1. `nora_job.py status <job_id>` → estado y `error_message`.
2. `nora_job.py logs <job_id>` → los logs completos del robot (con `--archived`
   si el job es antiguo y la retención ya los movió).
3. Si el proceso usa cola: `nora_queue.py stats <cola>` y
   `nora_queue.py list <cola> --status failed` (negocio: datos a corregir en
   el origen) / `--status dead_letter` (sistema: ambiente roto — credencial
   vencida, app caída, o clasificación equivocada).
4. Arregla la causa (p. ej. rota la credencial: `nora_asset.py set ...`).
5. Remedia en lote: `nora_queue.py action retry <cola> --status dead_letter`.
6. Relanza si hace falta: `nora_job.py rerun <job_id>` (acepta `--input`,
   `--machine`, `--priority`).
7. ¿El bug es del robot? Publica el fix (`nora package && nora release push`),
   apunta el proceso: `nora_process.py set-release`, y smoke:
   `nora_smoke.py --process ...`. ¿La release nueva salió peor? El mismo
   `set-release` con la versión anterior es tu rollback.

## Flota y versiones del agente (auto-update)

Desde el agente **0.8.0** la flota se actualiza sola: cada agente chequea la
versión current al arrancar y cada ~30 min; si hay una nueva entra en *drain*
(no toma jobs nuevos, **jamás interrumpe** los que corren), descarga el binario
verificando SHA-256 + firma Ed25519, y se reemplaza con swap atómico.

- **Ver el estado de la flota**: `nora_machine.py fleet-version` (versión
  current vs lo que reporta cada máquina por heartbeat). En la consola, la
  página Máquinas muestra el badge por máquina (ámbar = desactualizada,
  `v?` = pre-0.8.0).
- **Máquinas pre-0.8.0**: no tienen updater — requieren UNA reinstalación
  manual (zip de consola encima; conserva la identidad). Después, todo
  automático.
- **Publicar versión nueva del agente** (solo Valisoft): mergear el bump de
  `__version__` a main — el pipeline construye, verifica con smoke test,
  publica y registra solo. **Kill-switch** (platform admin):
  `POST /platform/agent-versions/{version}/set-current` — la flota converge a
  esa versión (downgrade incluido) en ≤30 min.
- **Alta de máquinas**: `nora_machine.py create --name ...` (muestra la
  machine_key una vez) + descarga del agente desde la consola.

## Otras superficies (mención breve)

| Qué | Dónde | Nota |
| --- | --- | --- |
| Importar items desde CSV | `POST /bulk/import/queue-items/{queue_id}` (sesión) o consola → Colas → Importar | ideal en migraciones cuando el cliente entrega CSV; alternativa: convertir a JSON y `nora_queue.py bulk --reference-field` |
| Exports (jobs, colas, auditoría) | `/bulk/export/*`, `GET /jobs/export/csv` (sesión/consola) | reportes |
| Analytics | `GET /processes/{id}/analytics`, `GET /queues/{id}/analytics`, `/dashboard/*` (sesión) | tendencias, duraciones, tasas de fallo |
| Feriados (para `--skip-holidays`) | `/holidays` CRUD (consola → Configuración) | cargar el calendario del país antes de usar skip_holidays |
| API keys por API | `POST /api/v1/settings/api-keys` (sesión, admin) + `GET .../available-scopes` | automatizar el bootstrap de integraciones |
| Grupos de máquinas | `/machine-groups` (consola) | organizar flotas grandes |
| Canales de notificación | `/notifications` CRUD + `POST /notifications/test/{id}` (consola) | job_failed/completed, machine_offline, schedule_missed |
| Anomalías | `GET /anomalies` (sesión/consola) | detección de duración/fallos atípicos — útil en diagnóstico |
| DAGs por API | `POST /dags`, `POST /dags/{id}/execute` (sesión) | flujos multi-proceso; diseño en consola |
| GraphQL (solo lectura) | `POST /graphql` (Bearer de sesión) | jobs/processes/machines/schedules/queues/dashboard_stats en una sola query |

## Webhooks salientes (NORA → tu sistema)

Canales de notificación (consola → Notificaciones): `webhook`, `slack`,
`teams`, `email`. Eventos: `job_failed`, `job_completed`, `machine_offline`,
`schedule_missed`.

Entrega webhook genérico: `POST` con body `{"event": "...", ...payload}` y, si
el canal tiene signing secret (`nora_whsec_...`):

```
X-NORA-Timestamp: <unix seconds>
X-NORA-Signature: sha256=HMAC_SHA256(secret, "<timestamp>.<raw_body>")
```

Verificación lista para copiar: `templates/snippets/webhook_verify.py`.
Solo URLs https públicas (SSRF-protected: IPs privadas bloqueadas).

## Webhook entrante (tu sistema → NORA)

Dos vías:
1. `POST /webhooks/trigger/{process_id}` con `X-API-Key` — body
   `{machine_id (requerido), input_data}`.
2. Trigger webhook (creado con `nora_trigger_mgmt.py create`):
   `POST /triggers/inbound/{token}` público con firma
   `X-Webhook-Signature: sha256=<HMAC-SHA256(secret, raw_body)>`. El payload
   JSON llega al robot como parte del input.

## Fallback por sesión (`nora login`) — qué degrada y qué no

La sesión del CLI (`~/.nora/credentials.json`, refresh rotativo que los
scripts guardan solos) da acceso a los endpoints internos de la consola,
respetando el rol del usuario. **No todos los subcomandos degradan** — tabla
honesta:

| Subcomando | API key | Fallback sesión |
| --- | --- | --- |
| `nora_list.py machines/processes` | ✓ | ✓ |
| `nora_list.py queues/schedules/jobs/triggers` | ✗ | ✓ (solo sesión) |
| `nora_trigger.py` / `nora_smoke.py` | ✓ | ✓ |
| `nora_job.py status/stop` | ✓ | ✓ |
| `nora_job.py rerun/respond/logs` | ✗ | ✓ (solo sesión; `logs` sin --archived intenta API key primero) |
| `nora_machine.py create/fleet-version` | ✗ | ✓ (solo sesión) |
| `nora_machine.py list` | ✓ | ✓ |
| `nora_queue.py create` | ✓ | ✓ |
| `nora_queue.py add/bulk/list/stats` | ✓ | ✗ (solo API key) |
| `nora_queue.py action` (retry/approve/reject/delete) | ✗ | ✓ (solo sesión) |
| `nora_asset.py get/set` | ✓ | set crea con sesión; get y update-por-nombre solo API key |
| `nora_process.py list/releases/create` | ✓ | ✓ |
| `nora_process.py active` | ✓ | ✗ |
| `nora_process.py set-release` | ✗ | ✓ (solo sesión) |
| `nora_schedule.py create` | ✓ | ✓ |
| `nora_schedule.py active` | ✓ | ✗ |
| `nora_trigger_mgmt.py` | ✓ | ✓ |

Ojo: los endpoints internos no son contrato público estable; para
integraciones permanentes usa siempre la API key.
