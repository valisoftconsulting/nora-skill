# RPA de escritorio Windows (pywinauto) en NORA

Para automatizar apps de escritorio (SAP GUI, ERPs legacy, apps internas .NET/
WinForms/WPF). Template listo: `templates/robot-desktop`.

## Decisión de herramienta

| Target | Herramienta |
| --- | --- |
| App Windows con controles reales (botones, campos) | **pywinauto backend="uia"** |
| App que no expone controles (Citrix, VM remota, canvas) | pyautogui + imágenes (último recurso: frágil) |
| Web dentro de un navegador | Playwright (`robot-browser`) — nunca escritorio |
| SAP GUI con scripting habilitado | API de SAP GUI Scripting (win32com) > pywinauto |

## Las 6 reglas que evitan robots frágiles

1. **`backend="uia"`** — el default (win32) no ve WPF/UWP/Qt moderno.
2. **Selectores, no coordenadas**: `child_window(auto_id=..., control_type=...)`
   o `title`/`title_re`. Las coordenadas se rompen con cualquier cambio de
   layout, DPI o resolución.
3. **Esperas explícitas, no sleeps**: `.wait("ready"|"visible"|"enabled", timeout=N)`
   y `wait_not("visible")` para cierres. Un `time.sleep(5)` es un bug latente.
4. **Una app, muchas transacciones**: abre la app en `open_app()` (context
   manager del template) UNA vez y procesa toda la cola; el kill va en el
   `finally` — cero ventanas zombis.
5. **Timeouts de UIA = excepción de SISTEMA** (la plataforma reintenta);
   valida los datos ANTES de tocar la UI y lanza `BusinessError` para datos
   malos.
6. **Ruta del .exe por asset** (`text`), título de ventana en config — nada
   hardcodeado.

## La sesión de la máquina NORA (importante)

El agente Windows desatendido ejecuta los robots dentro de una **sesión RDP
propia** a la resolución/DPI configurados en la consola (Máquinas → editar →
resolución). Implicaciones:

- `NORA_DISPLAY_WIDTH/HEIGHT` reflejan esa resolución — configura la misma en
  tu máquina de desarrollo para que los layouts coincidan.
- La sesión existe solo mientras corren jobs (el session manager la levanta y
  la baja); tu robot no debe asumir estado de UI previo — abre la app desde
  cero cada corrida.
- Si la app requiere permisos elevados o un usuario específico, configúralo en
  la máquina (auto-logon en la consola) — no en el robot.

## Cómo descubrir selectores

```powershell
# Opción 1: Inspect (Windows SDK) — árbol UIA completo, auto_id y control_type
# Opción 2: desde Python
py -m pywinauto.recorder            # graba interacciones y sugiere selectores
# Opción 3: volcar el árbol de la ventana
python -c "from pywinauto import Application; app=Application(backend='uia').connect(title_re='.*MiApp.*'); app.window(title_re='.*MiApp.*').print_control_identifiers(depth=3)"
```

## Snippets frecuentes

```python
# Campo de texto (limpiar antes de escribir)
campo = window.child_window(auto_id="txtNumero", control_type="Edit")
campo.set_text("")            # o campo.type_keys("^a{DELETE}")
campo.type_keys("F-001", with_spaces=True)

# Botón + esperar el resultado
window.child_window(title="Registrar", control_type="Button").click_input()
window.child_window(auto_id="lblOk").wait("visible", timeout=20)

# Menú
window.menu_select("Archivo->Exportar")

# Diálogo emergente (puede o no aparecer)
try:
    dlg = window.child_window(title="Confirmar", control_type="Window")
    dlg.wait("visible", timeout=3)
    dlg.child_window(title="Sí", control_type="Button").click_input()
except Exception:
    pass  # no apareció — flujo normal

# Grillas/tablas UIA
grid = window.child_window(control_type="DataGrid")
filas = grid.descendants(control_type="DataItem")
```

## Diagnóstico de fallos de escritorio

- **`ElementNotFoundError`/timeout**: el selector cambió o la app tardó.
  Captura evidencia en el except de sistema: `window.capture_as_image().save(...)`
  y súbela al log (`nora.log("error", ..., {"screenshot": "..."})`) antes del
  `fail_system`.
- **Funciona en dev, falla en la máquina**: casi siempre resolución/DPI
  distintos (iguala la configuración de la consola) o la app pide un diálogo
  de primera ejecución en ese perfil de usuario (córrela una vez a mano).
- **`ERROR: backend uia not found`**: falta `pywinauto` en requirements.txt o
  el venv del agente no lo instaló (revisa los logs del job).
