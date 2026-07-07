# Playwright en robots NORA: selectores estables y diagnóstico

Complemento de `templates/robot-browser` (que ya cablea el viewport a la
sesión de la máquina). Esto es el CÓMO escribir automatización web que no se
rompa a la semana.

## Jerarquía de selectores (de más a menos estable)

1. `page.get_by_test_id("registrar")` — si el sitio tiene data-testid, úsalo.
2. `page.get_by_role("button", name="Registrar")` — semántico, sobrevive
   rediseños de CSS.
3. `page.get_by_label("Número de factura")` / `get_by_placeholder(...)`.
4. `page.locator("#numero")` — IDs estables.
5. ❌ XPath posicional (`div[3]/span[2]`), clases generadas (`.css-x8k2j`),
   `nth()` sin ancla — se rompen solos.

Regla: si el selector describe QUÉ es el elemento (rol, etiqueta), sobrevive;
si describe DÓNDE está, muere.

## Esperas: Playwright ya espera — no le "ayudes"

- Las acciones (`click`, `fill`) auto-esperan visibilidad/actionability. Un
  `page.wait_for_timeout(5000)` es casi siempre un bug latente.
- Espera RESULTADOS, no tiempos: `expect(locator).to_be_visible()`,
  `page.wait_for_url("**/confirmacion")`,
  `page.wait_for_load_state("networkidle")` (con moderación).
- Para descargas/popups usa los context managers:
  `with page.expect_download() as d: page.click(...)`.

## Evidencia ante fallos (oro para el diagnóstico remoto)

En el `except` de sistema, antes del `fail_system`, captura pantalla — con los
logs del job es la diferencia entre adivinar y saber:

```python
except Exception as e:
    shot = workdir / f"error-{ref}.png"
    try:
        page.screenshot(path=str(shot), full_page=True)
        nora.log("error", f"Fallo en {ref}: {e}", {"screenshot": str(shot)})
    except Exception:
        nora.log("error", f"Fallo en {ref}: {e} (sin screenshot)")
    nora.fail_system(QUEUE, item, str(e))
```

Para depurar local: `nora dev run main.py --input '{"headless": false}'` abre
la ventana real; con `PWDEBUG=1 python main.py` tienes el inspector paso a paso.

## Sesiones y logins

- Credenciales SIEMPRE de un asset `credential`; loguea una vez en
  `initialize()` y reusa la página para todos los items.
- Si el sitio tiene MFA/captcha: sesión persistente
  (`browser.new_context(storage_state=...)`) sembrada una vez a mano en la
  máquina, o pedir al cliente una cuenta de servicio sin MFA — el robot no
  resuelve captchas.
- Cierres de sesión a mitad de corrida = excepción de sistema (el reintento
  vuelve a loguear porque `initialize()` corre en la re-ejecución del item).

## Estabilidad en las máquinas NORA

- El template ya fija `viewport = NORA_DISPLAY_WIDTH/HEIGHT` — misma geometría
  en dev y producción.
- `headless=True` en producción (input del template); los sitios que detectan
  headless suelen aceptar `chromium.launch(headless=False)` dentro de la
  sesión RDP de la máquina — es una sesión gráfica real.
- `python -m playwright install chromium` una vez por máquina (documéntalo en
  el README del robot; el agente instala pip deps, no navegadores).
- `page.set_default_timeout(30_000)` global (ya en el template) y timeouts
  puntuales mayores solo donde el sitio es lento de verdad.
