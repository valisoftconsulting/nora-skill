# Robot web (Playwright + cola)

Plantilla para automatización de navegador: Playwright con el **viewport
alineado a la resolución de la sesión de la máquina NORA**
(`NORA_DISPLAY_WIDTH/HEIGHT`) — selectores y screenshots estables entre tu
equipo y las máquinas del orquestador. El navegador se abre una vez y procesa
la cola item por item.

## Qué editas

| Archivo | Qué |
| --- | --- |
| `config.py` | cola, asset de URL y asset de credenciales |
| `transactions.py` | `initialize()` (login) y `process_transaction()` |

`main.py`, `browser.py` y `nora_helpers.py` no se tocan.

## Antes de correr

```bash
pip install -r requirements.txt
python -m playwright install chromium     # una vez por máquina
```

Crea los assets (`APP_URL` tipo text, `APP_CREDENCIALES` tipo credential) y la
cola; decláralos en `required_assets` del proceso.

## Ciclo de trabajo

```bash
python -m pytest tests/ -q     # lógica con Page fake, sin navegador
python main.py                 # local degradado
nora dev run main.py --input '{"headless": false}' --assets APP_URL,APP_CREDENCIALES -e dev
nora package && nora release push
```

Tip de depuración: `headless=false` en local abre la ventana real.
