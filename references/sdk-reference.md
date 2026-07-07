# Referencia del SDK `nora_agent.sdk`

> Verificado contra **nora-sdk 0.7.9** (2026-07-07). Si sospechas drift, corre
> `python3 scripts/self_check.py` — compara estas firmas con el SDK instalado.

```python
from nora_agent import sdk
```

Instalación para desarrollo local: `pip install nora-sdk` (Python ≥ 3.10,
única dependencia: httpx). En la máquina del agente el SDK se inyecta solo.

**Comportamiento en dev local** (sin `NORA_JOB_ID`): `log`, `update_progress` y
`set_output` degradan a `print()`; las funciones de cola/assets requieren un
token (usa `nora dev run`). Las funciones marcadas ⚙ lanzan `RuntimeError`
sin job gestionado.

## Argumentos in/out

### `get_inputs() -> 'dict[str, Any]'`
Todos los argumentos de entrada del job (lee `NORA_INPUT`, sin red). `{}` si no hay.

### `get_input(name: 'str | None' = None, default: 'Any' = None) -> 'Any'`
Un argumento por nombre con default: `sdk.get_input("mes")`, `sdk.get_input("reintentos", 3)`.

### `set_output(key_or_dict: "'str | dict[str, Any]'", value: 'Any' = None) -> 'None'`
Publica salidas del job (merge server-side): `sdk.set_output("total", 42)` o
`sdk.set_output({"total": 42, "resumen": "..."})`.

## Assets (credenciales/config cifradas)

### `get_asset(name: 'str', environment: 'str' = 'production') -> 'dict[str, Any]'`
Devuelve `{name, type, environment, value, username?}` descifrado. Primero mira
`NORA_ASSETS` (pre-cargado por el agente); si no, va a la API. El token del job
solo puede leer los assets declarados en `required_assets` del proceso.
Tipos: `text | credential | secret | integer | number | bool` (value ya casteado).

## Colas

### `get_queue_item(queue_name: 'str') -> 'dict[str, Any] | None'`
Reclama el siguiente item (status → `in_progress`). `None` si la cola está vacía.
Dos performers en paralelo nunca reciben el mismo item.

### `complete_queue_item(queue_name: 'str', item_id: 'str', result: 'dict[str, Any]') -> 'None'`
Marca el item como `completed` con su resultado.

### `fail_queue_item(queue_name: 'str', item_id: 'str', error_message: 'str', exception_type: 'str' = 'system') -> 'None'`
Marca el item como fallido. **La decisión más importante del robot**:
- `exception_type="business"` → dato inválido, TERMINAL, no se reintenta.
- `exception_type="system"` → fallo transitorio, la plataforma reintenta hasta
  `max_retries` de la cola y luego lo manda a `dead_letter`.

### `add_queue_item(queue_name: 'str', data: 'dict[str, Any]', priority: 'int' = 3, reference: 'str | None' = None, deadline: 'Any' = None, postpone: 'Any' = None) -> 'dict[str, Any]'`
Encola un item. `priority`: 1=baja, 3=normal, 5=urgente. `reference` = clave de
idempotencia/trazabilidad. `deadline`/`postpone` aceptan datetime o ISO-8601.

### `add_queue_items(queue_name: 'str', items: 'list[dict[str, Any]]', priority: 'int' = 3) -> 'int'`
Encola en bulk (máx 1000 por llamada). Devuelve cuántos agregó.

### `queue_stats(queue_name: 'str') -> 'dict[str, int]'`
`{"new", "in_progress", "completed", "failed", "pending_review", "dead_letter", "total"}`.

### `queue_pending(queue_name: 'str') -> 'int'`
Atajo: items en status `new`.

## Revisión humana (human-in-the-loop sobre colas)

### `send_queue_item_for_review(queue_name: 'str', item_id: 'str') -> 'dict[str, Any]'`
Manda el item a `pending_review` — un operador lo aprueba/rechaza en la consola
(o desde Slack/Teams si hay canal configurado).

### `wait_for_queue_review(queue_name: 'str', item_id: 'str', poll_interval: 'float' = 5.0, timeout: 'float' = 3600.0) -> 'str'`
Bloquea hasta el veredicto: `"approved"` o `"rejected"`. `TimeoutError` si expira.

## Logging y progreso

### `log(level: 'str', message: 'str', data: 'dict[str, Any] | None' = None) -> 'None'`
Log estructurado al dashboard (`info|warning|error`). `data` viaja como JSON.

### `update_progress(percent: 'int', message: 'str | None' = None) -> 'None'`
Barra de progreso del job (0–100, se clampa).

## Control del job ⚙

### `get_job_id() -> 'str | None'`
UUID del job actual (`None` en dev local).

### `get_job_signal() -> 'str'`
`"none" | "stop" | "kill"` — la señal pedida desde el dashboard.

### `should_stop() -> 'bool'`
`True` si pidieron stop/kill. **Chequéalo en cada iteración de tus loops** y
cierra ordenadamente.

## Input atendido (attended) ⚙

### `request_user_input(prompt: 'str', options: 'list[str] | None' = None) -> 'dict[str, Any]'`
Publica una pregunta al operador (no bloquea).

### `wait_for_user_input(poll_interval: 'float' = 5.0, timeout: 'float' = 3600.0) -> 'Any'`
Espera la respuesta. `TimeoutError` si expira.

### `ask_user(prompt: 'str', options: 'list[str] | None' = None, poll_interval: 'float' = 5.0, timeout: 'float' = 3600.0) -> 'Any'`
Conveniencia request+wait; devuelve el valor directo:
`if sdk.ask_user("¿Continúo?", ["Sí", "No"]) == "No": ...`

## Infraestructura

### `check_for_update(current_version: 'str') -> 'dict[str, Any]'`
Usada por el agente para auto-update; un robot normal no la necesita.

## Variables de entorno del runtime

El agente inyecta al subproceso del robot (allowlist, NUNCA el entorno completo):

| Variable | Contenido |
| --- | --- |
| `NORA_JOB_ID` | UUID del job |
| `NORA_API_URL` | Base de la API |
| `NORA_EXEC_TOKEN` | Token POR JOB, acotado a assets/entorno del proceso, expira con el job |
| `NORA_INPUT` | JSON con `input_data` |
| `NORA_ASSETS` | JSON con los assets declarados (pre-fetch, sin red) |
| `NORA_DISPLAY_WIDTH/HEIGHT/DEPTH/SCALE` | Resolución de la sesión de la máquina |

Nunca leas estas variables a mano: usa las funciones del SDK (o `nora_helpers`).
