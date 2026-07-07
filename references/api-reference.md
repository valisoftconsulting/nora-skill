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
| `/queues/by-name/{n}/items/bulk` | POST | `queues:write` | 20 | `nora_queue.py bulk` |
| `/schedules/create` | POST | `schedules:manage` | 10 | `nora_schedule.py create` |
| `/schedules/{id}/active` | PATCH | `schedules:manage` | 30 | `nora_schedule.py active` |
| `/triggers/create` | POST | `triggers:manage` | 10 | `nora_trigger_mgmt.py create` |
| `/triggers/{id}/rotate-secret` | POST | `triggers:manage` | 10 | `nora_trigger_mgmt.py rotate-secret` |
| `/webhooks/trigger/{process_id}` | POST | (feature webhooks) | 60 | — (para sistemas externos) |

Detalles de payloads: docs vivas → `api/gestion`, `api/disparar-jobs`,
`api/colas`, `api/assets`.

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

## Fallback por sesión (`nora login`)

Los scripts intentan primero la API key; si falta o no tiene el scope, usan la
sesión del CLI (`~/.nora/credentials.json`) contra los endpoints internos de
la consola, respetando el rol del usuario (crear procesos/assets requiere
admin). El refresh token rota en cada uso — los scripts guardan el nuevo
automáticamente. Ojo: los endpoints internos no son contrato público estable.
