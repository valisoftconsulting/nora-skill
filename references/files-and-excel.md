# Archivos, Excel y CSV en robots NORA

El 80 % del RPA real mueve archivos: leer un Excel del contable, volcar un CSV
a una cola, dejar un reporte donde alguien lo encuentre. Patrones probados:

## Rutas: nunca hardcodees, nunca asumas tu HOME

- Las rutas de entrada/salida van por **input** (cambian por corrida: "procesa
  este archivo") o por **asset `text`** (fijas por entorno: carpeta de red).
- La ruta existe en LA MÁQUINA del agente, no en tu laptop. `C:\Users\kathy\...`
  es un bug: usa el asset por entorno.
- Directorio de trabajo temporal del robot: `tempfile.mkdtemp()` y limpia en
  el `end()`/`finally`. No escribas junto al código (el paquete es de solo
  lectura conceptualmente).

```python
import tempfile
from pathlib import Path

carpeta_entrada = Path(nora.asset("CARPETA_FACTURAS")["value"])
workdir = Path(tempfile.mkdtemp(prefix="mi-robot-"))
```

## Excel: openpyxl vs pandas

| Necesitas | Usa |
| --- | --- |
| Leer/escribir celdas, formatos, varias hojas | `openpyxl` |
| Transformar datos tabulares (filtrar, agrupar, joins) | `pandas` (+ `openpyxl` como engine) |
| Archivos .xls viejos | `pandas` con `xlrd` (o pedir .xlsx) |

```python
# Leer un Excel a registros (pandas)
import pandas as pd
df = pd.read_excel(ruta, sheet_name="Facturas", dtype={"ruc": str})  # ¡dtype str para códigos!
registros = df.to_dict("records")

# Escribir un reporte con formato (openpyxl)
from openpyxl import Workbook
wb = Workbook(); ws = wb.active
ws.append(["Referencia", "Estado", "Error"])
for r in resultados:
    ws.append([r["ref"], r["estado"], r.get("error", "")])
wb.save(workdir / "reporte.xlsx")
```

Gotchas de Excel que rompen robots: RUC/códigos leídos como float
(`dtype=str`), fechas que pandas interpreta con el locale equivocado
(`parse_dates` + `dayfirst=True`), celdas combinadas (evítalas en la fuente),
y archivos ABIERTOS por un humano en la máquina (lock de Windows → error de
sistema, el reintento de la plataforma suele salvarlo).

## CSV → cola (el patrón dispatcher correcto)

NO proceses el CSV en un loop dentro del robot: cárgalo a la cola con
`reference` y deja que el performer lo consuma (reintentos, auditoría,
paralelismo gratis).

```python
import csv

def fetch_records() -> list[dict]:
    with open(ruta_csv, newline="", encoding="utf-8-sig") as f:  # -sig: BOM de Excel
        return list(csv.DictReader(f, delimiter=";"))            # Excel LATAM usa ;
```

Desde fuera del robot: `nora_queue.py bulk facturas --file items.json
--reference-field numero`, o el import de CSV de la consola
(`Colas → Importar`, endpoint `/bulk/import/queue-items/{queue_id}`).

## Salidas durables

El disco de la máquina NO es un entregable: cualquier archivo que un humano
necesite debe terminar en un destino durable — carpeta de red (asset con la
ruta), SharePoint/Drive/S3 vía API (credenciales en assets), o correo. Deja en
`set_output` la RUTA/URL final para que quede en el job:

```python
nora.set_output("reporte", str(destino_final))
```

## El archivo como disparador

Si el proceso empieza "cuando llega un archivo a la carpeta X": no hagas un
robot que sondee — usa un **trigger file watcher** de NORA (consola →
Triggers, asignado a la máquina que ve esa carpeta). El robot recibe la ruta
del archivo en su input.

## Checklist de archivos

- [ ] Encodings: `utf-8-sig` para CSV que tocó Excel; `latin-1` para sistemas legacy.
- [ ] Delimitador `;` en CSV de Excel con locale español.
- [ ] Códigos/RUC como `str`, nunca float.
- [ ] Archivo en uso por humano = excepción de sistema (reintenta), no business.
- [ ] Limpieza del workdir temporal en `end()`.
- [ ] Nada se queda solo en el disco de la máquina: salida a destino durable.
