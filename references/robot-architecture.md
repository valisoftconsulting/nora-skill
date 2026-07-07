# Anatomía de un robot NORA profesional

## Modelo mental

Un robot NORA es un **proyecto Python normal** + un manifiesto `nora.json`.
Se empaqueta en zip (`nora package`), se publica como **Release** de un
**Package**, un **Process** apunta a esa release con su configuración
(timeout, retries, assets requeridos), y cada ejecución es un **Job** en una
**Machine** (Mac/Windows con el agente instalado).

```
Package ──▶ Release (zip + entry_point + argumentos) ──▶ Process ──▶ Job
                                                            ▲
                                    Schedule (cron) ────────┤
                                    Trigger (webhook/cola) ─┘
```

## Estructura recomendada

```
mi-robot/
├── nora.json            # contrato: nombre, versión, entry point, args in/out
├── main.py              # orquesta — se lee de arriba a abajo
├── config.py            # constantes (nombre de cola, flags) — sin lógica
├── nora_helpers.py      # ÚNICO punto de contacto con la plataforma (copia del skill)
├── <modulos>.py         # lógica de negocio (transactions.py, browser.py, ...)
├── requirements.txt     # deps con versiones fijadas (si hay)
├── .noraignore          # exclusiones del paquete
└── tests/               # pytest de la lógica, sin plataforma
```

**Regla de oro**: la lógica de negocio JAMÁS llama al SDK directamente —
siempre a través de `nora_helpers.py`. Beneficios: corre sin credenciales
(`python main.py`), se testea con un fake, y un cambio del SDK se absorbe en
un solo archivo.

## Esquema de `nora.json`

```json
{
  "name": "mi-robot",
  "version": "1.0.0",
  "entry_point": "main.py",
  "inputs": [
    { "name": "mes", "type": "text", "required": true, "description": "Mes YYYY-MM" },
    { "name": "reintentos", "type": "integer", "default": 3, "description": "..." },
    { "name": "enviar_correo", "type": "bool", "default": true, "description": "..." }
  ],
  "outputs": [
    { "name": "procesados", "type": "integer" },
    { "name": "resumen", "type": "text" }
  ]
}
```

- Tipos permitidos: `text`, `integer`, `number`, `bool` (alias: string/int/float/boolean).
- Cada argumento: `{name, type, required?, default?, description?}`.
- El backend deriva un JSON Schema y **valida `input_data` en TODAS las vías**
  (formulario del panel, API, webhook, schedule). Argumento requerido faltante
  o tipo incorrecto → 422 antes de llegar a la máquina.
- La consola pinta el formulario de lanzamiento con estas descriptions:
  escríbelas siempre.
- `entry_point` relativo a la raíz del zip, sin `..`. Default `main.py` con
  `def main()` + `if __name__ == "__main__": main()`.

Valida siempre con `python3 scripts/validate_manifest.py <carpeta>` (sin red).

## Tabla de decisión de patrón

| Situación | Template |
| --- | --- |
| Corrida única: reporte, descarga, conciliación pequeña | `robot-minimal` |
| N items con reintentos/auditoría/estado por item | `robot-transactional` |
| Fuente de datos separada del procesamiento; escalar en paralelo | `robot-dispatcher-performer` |
| Automatización de navegador (web) sobre cola | `robot-browser` (Playwright + viewport de sesión) |

Regla práctica: **>20 items, o necesidad de reintentos por item, o auditoría
de qué pasó con cada registro → usa cola** (ver `queues-and-exceptions.md`).

## Reglas de robots largos

- `should_stop()` al inicio de cada iteración → cierre ordenado ante Stop.
- `update_progress(pct, msg)` para que el operador vea avance real.
- `log()` con `data` estructurada en los hitos (inicio, por item, fin).
- Reintentos de items: los hace la PLATAFORMA (max_retries de la cola).
  No escribas `for intento in range(3)` alrededor de una transacción.
- El proceso define `timeout_seconds`: al excederlo el job muere. Dimensiona
  el timeout o divide el trabajo.

## Attended (human-in-the-loop)

Dos mecanismos, no los confundas:
- **`ask_user(prompt, options)`**: pausa el job hasta que el operador responda
  en la consola. Para decisiones puntuales de una corrida.
- **`send_for_review` + `wait_review`** (colas): el item queda `pending_review`
  y un revisor aprueba/rechaza (consola, Slack o Teams). Para aprobaciones
  por transacción (facturas, pagos).

Ambos aceptan timeout. Con `nora_helpers`, `wait_review` devuelve
`"approved" | "rejected" | "timeout"` (y `"approved"` en dev local sin SDK):
maneja el `"timeout"` explícitamente — el helper no decide por ti. Un operador
también puede responder un `ask_user` pendiente desde fuera con
`scripts/nora_job.py respond <job_id> --value "..."`.

## Pipelines multi-proceso (DAGs) y notificaciones

- Si el pipeline son **varios procesos encadenados** con dependencias
  (extraer → transformar → registrar en robots distintos), NO lo simules con
  triggers ni `on_success_trigger`: NORA tiene **Flujos DAG** (se diseñan en
  la consola; ver docs vivas `guia/flujos-dag`). Para el encadenado simple de
  dos procesos sí basta `on_success_trigger_process_id` del proceso.
- **Alertas** (`job_failed`, `job_completed`, `machine_offline`,
  `schedule_missed`) se configuran como canales de notificación
  (webhook/Slack/Teams/email) en la consola → Notificaciones; el robot no
  necesita enviar correos por su cuenta.

## Desarrollo local y depuración

```bash
python main.py                                   # sin credenciales (helpers degradan)
nora dev run main.py --input '{"mes":"2026-07"}' # token dev real, entorno dev
nora dev run main.py --assets CRED1,CRED2 -e staging
nora dev env --write .env                        # para breakpoints en el IDE
```

`nora dev run` acuña un token de desarrollo (entornos dev/staging solamente,
producción prohibida) e inyecta las mismas env vars que el agente. Con
`nora dev env --write .env` + `envFile` en el launch.json de VS Code depuras
con breakpoints contra colas y assets reales de dev.

## Resolución de pantalla (UI automation)

El agente inyecta `NORA_DISPLAY_WIDTH/HEIGHT`. Si tu robot usa navegador o
escritorio, fija el viewport a esos valores para que los selectores sean
estables entre máquinas:

```python
import os
ancho = int(os.environ.get("NORA_DISPLAY_WIDTH", 1920))
alto = int(os.environ.get("NORA_DISPLAY_HEIGHT", 1080))
```
