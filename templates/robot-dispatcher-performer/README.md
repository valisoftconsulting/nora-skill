# Robot dispatcher + performer

Plantilla para el patrón clásico de RPA a escala: un **dispatcher** que puebla
la cola desde la fuente (CSV, API, BD) y **performers** que la consumen en
paralelo. Un solo paquete, el modo se elige con el input `mode`.

## Qué editas

| Archivo | Qué |
| --- | --- |
| `config.py` | Nombre de la cola y campo de referencia (idempotencia) |
| `dispatcher.py` | `fetch_records()` y `to_queue_item()` |
| `performer.py` | `process_item()` (lanza `BusinessError` para datos inválidos) |

`main.py` y `nora_helpers.py` no se tocan.

## Idempotencia

El dispatcher encola con `reference=<REFERENCE_FIELD>`: si corre dos veces
sobre la misma fuente, los items repetidos no duplican trabajo.

## Escalar en NORA

1. `nora package && nora release push` (un solo paquete).
2. Crea DOS procesos desde la misma release:
   - `mi-robot — dispatcher` (schedule, p. ej. 7:00 am).
   - `mi-robot — performer` (disparado por trigger de cola o lanzado N veces
     en máquinas distintas).
3. Los performers en paralelo no se pisan: `claim_next` entrega cada item a
   un solo robot.

## Ciclo de trabajo

```bash
python -m pytest tests/ -q
python main.py
nora dev run main.py --input '{"mode": "auto"}'
nora package && nora release push
```
