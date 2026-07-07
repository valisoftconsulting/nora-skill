# Colas, transacciones y excepciones negocio/sistema

## Ciclo de vida de un QueueItem

```
new ──claim──▶ in_progress ──complete──▶ completed
                   │
                   ├─fail(business)──▶ failed            (TERMINAL)
                   ├─fail(system)───▶ new (reintento) …──▶ dead_letter (agotó max_retries)
                   └─review─────────▶ pending_review ──approve──▶ new
                                                     └─reject───▶ failed
```

- `max_retries` se configura EN LA COLA (0–10, default 3).
- `priority`: 1=baja, 3=normal, 5=urgente — los urgentes se reclaman primero.
- `reference`: clave de idempotencia y trazabilidad (nº de factura, ID de fila).
- `postpone`: no procesar antes de X. `deadline`: fecha límite (SLA).

## Árbol de decisión: ¿business o system?

Pregunta única: **¿reintentar con LOS MISMOS datos puede tener éxito?**

- **NO** → `business` (terminal): factura sin RUC, cliente inexistente, monto
  negativo, formato inválido, regla de negocio incumplida.
- **SÍ** → `system` (reintenta): timeout de red, app caída, selector que no
  apareció, sesión expirada, disco lleno.

Errores comunes de clasificación:
- Marcar `system` un error de validación → el item se reintenta inútilmente
  3 veces y ensucia el dead_letter. Los datos malos son `business`.
- Marcar `business` un timeout → pierdes el reintento gratis que te habría
  salvado la transacción.
- Capturar `Exception` y completar el item igual → transacciones "completadas"
  que en realidad fallaron. Nunca tragues excepciones en el loop.

## Loop transaccional canónico

```python
while True:
    if nora.should_stop():
        break
    item = nora.claim_next(QUEUE)
    if item is None:
        break                                   # cola vacía
    try:
        result = process_transaction(item["data"], context)
        nora.complete(QUEUE, item, result)
    except BusinessError as e:
        nora.fail_business(QUEUE, item, str(e))
    except Exception as e:
        nora.fail_system(QUEUE, item, str(e))
```

Con `nora_helpers.py` este loop ya viene resuelto en los templates
`robot-transactional` y `robot-dispatcher-performer` — no lo reescribas.

## Idempotencia del dispatcher

Encola siempre con `reference=<id único del registro>`. Si el dispatcher corre
dos veces (schedule duplicado, reintento del job), el item repetido es
detectable y el performer puede saltarlo. Además `reference` permite buscar el
item de una factura concreta en la consola.

## Revisión humana por transacción

```python
nora.send_for_review(QUEUE, item)
decision = nora.wait_review(QUEUE, item, timeout=3600)
if decision == "approved":
    ...registrar...
    nora.complete(QUEUE, item, {"registrado": True})
# "rejected" → el item ya queda failed; solo loggea
```

Configura revisores de la cola en la consola. Si hay canal Slack/Teams, la
aprobación llega como tarjeta con botones.

## Gestión de la cola desde fuera del robot

| Acción | Herramienta |
| --- | --- |
| Crear cola | `scripts/nora_queue.py create facturas --max-retries 3` |
| Encolar 1 item | `scripts/nora_queue.py add facturas --data '{...}' --reference F-001` |
| Encolar CSV/lote | `scripts/nora_queue.py bulk facturas --file items.json` |
| Ver por estado | `scripts/nora_queue.py list facturas --status dead_letter` |
| Conteos | `scripts/nora_queue.py stats facturas` |

## Diagnóstico post-corrida

1. `stats` — ¿cuántos en `failed` y `dead_letter`?
2. `list --status failed` — errores de negocio: revisar `error_message` de cada
   item; son datos a corregir en el origen.
3. `list --status dead_letter` — errores de sistema persistentes: ambiente roto
   (credencial vencida, app caída) o clasificación equivocada.
4. En la consola se pueden reintentar (bulk retry) los dead_letter tras
   arreglar la causa.
