# Eval E — Robot web/escritorio con scaffolding

**Prompt de prueba (web):**
> Necesito un robot que entre a nuestro portal de proveedores, registre cada
> orden de compra de un Excel y me deje un resumen. Las credenciales del portal
> no van en el código.

**El agente debe:**
1. `scripts/doctor.py` y entrevista mínima; identificar target **web** → template
   `robot-browser`, y fuente **Excel** → `references/files-and-excel.md`.
2. Crear el robot con `scripts/new_robot.py ordenes-portal --template browser
   --queue ordenes-compra` (no copiar a mano dejando el nombre del template).
3. Excel → cola: leer con pandas/openpyxl (RUC/códigos como `str`), cargar con
   `reference` (patrón dispatcher), credenciales en asset `credential`.
4. Selectores estables (`get_by_role`/`get_by_label`, no XPath posicional) y
   captura de screenshot en el except de sistema (`browser-patterns.md`).
5. Validación en pirámide (pytest con page fake corre sin navegador).

**Falla si:** copia el template sin renombrar; procesa el Excel en un loop en
vez de encolarlo; hardcodea credenciales o la ruta del Excel; usa selectores
posicionales; no captura evidencia ante fallos.

---

**Prompt de prueba (escritorio):**
> Automatiza el registro en nuestro ERP de escritorio (una app Windows vieja);
> los datos vienen de una cola.

**El agente debe:**
1. Target **escritorio Windows** → template `robot-desktop` +
   `references/desktop-windows.md`; `new_robot.py ... --template desktop`.
2. pywinauto `backend="uia"`, selectores por `auto_id`/`title`/`control_type`,
   esperas explícitas (nada de `time.sleep`), ruta del .exe en asset.
3. Explicar que corre en la sesión RDP de la máquina a la resolución
   configurada y que los timeouts de UIA son excepción de **sistema**.

**Falla si:** usa coordenadas absolutas o sleeps fijos; hardcodea la ruta del
ejecutable; clasifica un timeout de UIA como business; recomienda Playwright
para una app de escritorio.
