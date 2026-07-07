# Robot de escritorio Windows (pywinauto + cola)

Plantilla para automatizar aplicaciones de escritorio Windows (SAP GUI, ERPs
legacy, apps internas) con **pywinauto backend UIA**, integrada a la cola
transaccional de NORA y a la sesión RDP de la máquina.

## Qué editas

| Archivo | Qué |
| --- | --- |
| `config.py` | cola, asset con la ruta del .exe, título de la ventana |
| `transactions.py` | `process_transaction()` con selectores UIA |

`main.py`, `desktop.py` y `nora_helpers.py` no se tocan.

## Reglas de escritorio (léelas — evitan el 90 % de los dolores)

1. **backend="uia" siempre** (ya cableado en `desktop.py`).
2. **Cero coordenadas absolutas / cero sleeps fijos**: selectores por
   `auto_id`/`title`/`control_type` + `wait("ready"|"visible", timeout=N)`.
3. **Descubre selectores** con `inspect.exe` (Windows SDK) o
   `py -m pywinauto.recorder`.
4. La máquina NORA ejecuta el robot en una **sesión RDP** a la resolución
   configurada en la consola (`NORA_DISPLAY_WIDTH/HEIGHT`) — misma resolución
   en dev y producción = mismos layouts.
5. La ruta del ejecutable va en un **asset** (`APP_EXE_PATH`), no hardcodeada.

Guía completa: `references/desktop-windows.md` del skill.

## Ciclo de trabajo

```bash
python -m pytest tests/ -q          # lógica con ventana fake, en cualquier SO
nora dev run main.py                # en una máquina Windows con la app
nora package && nora release push
```
