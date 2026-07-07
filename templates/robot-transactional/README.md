# Robot transaccional (estilo REFramework)

Plantilla para procesos que consumen una **cola** item por item, con
clasificación de errores negocio/sistema y reintentos delegados a la
plataforma. Es el equivalente NORA del REFramework de UiPath:

| REFramework (UiPath) | Aquí |
| --- | --- |
| Init | `transactions.initialize()` |
| Get Transaction Data | `nora.claim_next(QUEUE)` en `main.py` |
| Process Transaction | `transactions.process_transaction()` |
| SetTransactionStatus Success | `nora.complete(...)` |
| BusinessRuleException | `raise BusinessError(...)` → `fail_business` (terminal) |
| ApplicationException | cualquier otra excepción → `fail_system` (reintenta) |
| End Process | `transactions.end()` |

**Solo editas `transactions.py`** (y `config.py`). `main.py` y
`nora_helpers.py` no se tocan.

## Antes de correr

1. Crea la cola en NORA (consola, o `nora_queue.py create mi-cola --max-retries 3`).
2. Ajusta `QUEUE` en `config.py`.
3. Crea los assets que necesites y decláralos en `required_assets` del proceso.

## Ciclo de trabajo

```bash
python -m pytest tests/ -q        # lógica de negocio sin plataforma
python main.py                    # smoke local sin credenciales
nora dev run main.py              # corrida real contra cola/assets de dev
nora package && nora release push # publicar
```
