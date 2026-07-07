# Migrar un script Python suelto a robot NORA

Objetivo: conservar la lógica que YA funciona (selenium/playwright, pandas,
requests...) y darle contrato, credenciales seguras, observabilidad y
reintentos de plataforma. **La lógica se muda, no se reescribe.**

## Procedimiento (7 pasos)

### 1. Inventario (ANTES de tocar código — presentar al usuario)

Lee el script completo y produce esta tabla para aprobación:

| Qué buscar | Se convierte en |
| --- | --- |
| Valores hardcodeados que cambian por corrida (fechas, rutas, flags) | `inputs` de nora.json |
| Credenciales, tokens, URLs de sistemas (hardcoded, .env, input()) | **Assets** (`credential`/`secret`/`text`) |
| `argv` / `argparse` / `input()` | `inputs` (los jobs no son interactivos*) |
| `print()` / `logging` | `nora.log()` |
| Resultado final (archivo, return, print resumen) | `outputs` + destino durable |
| Loop sobre filas/registros | ¿Cola? (regla del paso 3) |
| `try/except` existentes | clasificar business/system |
| `time.sleep()` esperando horarios / cron externo | Schedule de NORA |
| Notificaciones por smtplib/slack manuales | canales de notificación del orquestador |
| Imports de terceros | `requirements.txt` con versiones |

(*) Si el script pregunta algo a un humano a mitad de corrida → `ask_user()`.

### 2. Elegir template

Sin loop de registros → `robot-minimal`. Con loop → regla del paso 3.

### 3. ¿Cola o no cola?

Usa cola si: **>20 items por corrida**, o necesitas **reintentos por item**, o
**auditoría de qué pasó con cada registro**, o quieres **paralelizar**.
Si es cola: ¿la fuente la lee el mismo robot? → `robot-transactional` con carga
inicial. ¿Fuente y proceso separados o escalar? → `robot-dispatcher-performer`.

### 4. Definir el contrato primero

Escribe `nora.json` (inputs/outputs del inventario) y valida con
`validate_manifest.py` ANTES de portar lógica.

### 5. Portar la lógica

- Copia el template elegido y mueve las funciones del script tal cual a
  `transactions.py` / `process_item()` / el cuerpo de `main.py`.
- Reemplaza: hardcodes → `nora.get_input(...)`; credenciales →
  `nora.asset(...)`; prints → `nora.log(...)`; resumen final →
  `nora.set_output(...)`.
- El acceso a plataforma SOLO vía `nora_helpers.py`.
- Crea los assets (`nora_asset.py set ... --env dev` primero) y la cola si aplica.

### 6. Clasificar excepciones

Recorre cada `except` original y decide con el árbol de
`queues-and-exceptions.md`: ¿dato malo (business) o infraestructura (system)?
Los `except: pass` del script original son deuda: conviértelos en
`fail_*` con mensaje, o déjalos propagar.

### 7. Validar en pirámide

`testing-and-validation.md` niveles 1→6. El nivel 3 (`python main.py`) debe
reproducir el comportamiento del script original con datos de prueba antes de
publicar.

## Olores frecuentes

| Olor en el script | Solución NORA |
| --- | --- |
| `usuario = "admin"; clave = "1234"` | asset `credential` + `required_assets` |
| `webdriver.Chrome()` sin tamaño fijo | viewport = `NORA_DISPLAY_WIDTH/HEIGHT` |
| `while True: ... time.sleep(3600)` | quitar el loop; schedule cron cada hora |
| Escribe resultado en `C:\Users\yo\...` | ruta por input/asset; salida durable |
| `except Exception: continue` | `fail_system` con mensaje (queda auditado) |
| Reintentos manuales `for i in range(3)` | quitar; `max_retries` de la cola |
| CSV local como estado ("ya procesados") | la cola ES el estado; reference=id |
