# Robot mínimo

Plantilla para jobs puntuales **sin colas**: recibe argumentos, hace su trabajo,
publica salidas. Úsala cuando el proceso corre de una sola pasada (un reporte,
una descarga, una conciliación pequeña).

## Estructura

| Archivo | Rol |
| --- | --- |
| `nora.json` | Contrato: nombre, versión, entry point, argumentos in/out |
| `main.py` | Lógica del robot |
| `nora_helpers.py` | Único punto de contacto con la plataforma (no lo edites) |

## Ciclo de trabajo

```bash
python main.py                                        # prueba sin credenciales
nora dev run main.py --input '{"mes": "2026-07"}'     # prueba real en entorno dev
nora package                                          # empaqueta dist/<name>-<ver>.zip
nora release push                                     # publica (requiere rol admin)
```

Si tu robot usa dependencias externas, créale un `requirements.txt` con
versiones fijadas — el agente crea el venv e instala en la máquina.
