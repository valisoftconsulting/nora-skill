# CLI `nora` y pipeline de despliegue

> CLI incluida en `pip install nora-sdk` (o `nora-agent`). Verificado contra
> nora-sdk 0.7.9.

## Comandos

### `nora login`
Device flow (RFC 8628): muestra un código, abre el navegador, sin contraseña
en la terminal. Sesión en `~/.nora/credentials.json` (0600, refresh token que
ROTA en cada uso). Headless/CI: `nora login --email x --password y` (+ MFA si
aplica). `nora logout` borra la sesión.

### `nora dev run <entry.py>`
Corre el robot LOCALMENTE con un token de desarrollo real (entornos
`dev`/`staging`; producción prohibida):

```bash
nora dev run main.py --input '{"mes": "2026-07"}' --assets CRED1,CRED2 -e dev
```

Flags: `--environment/-e dev|staging` · `--assets a,b` (a cuáles puede acceder)
· `--ttl` (default 1800s) · `--input '<json>'` · args extra para el script.

### `nora dev env`
Imprime/escribe las env vars para depurar desde el IDE:

```bash
nora dev env --write .env          # + envFile en launch.json → breakpoints
nora dev env --format powershell   # dotenv | bash | powershell
```

TTL default 8h. NUNCA comitees ese `.env` (el escáner de secretos lo bloquea).

### `nora package [path]`
Empaqueta el robot en `dist/<name>-<version>.zip`:
- **Versionado semver automático**: primera vez 1.0.0, luego bump `patch`
  (cambia con `--bump major|minor|patch|none` o `--version X.Y.Z`). Persiste
  en `nora.json`.
- **Exclusiones default**: .venv, __pycache__, .git, node_modules, cachés,
  `.env*`, `.nora/`, credentials.json. Extra: `.noraignore` (sintaxis
  gitignore), `--exclude GLOB`, `--gitignore`.
- **Escaneo de secretos**: aborta si detecta private keys, `nora_ak_...`,
  tokens NORA o AWS keys (`--allow-secrets` para forzar — casi nunca).
- Warnings: falta requirements.txt con deps de terceros; zip > 500 MB
  descomprimido (el agente lo rechazaría).
- `--list` = dry-run (qué entraría al zip).

### `nora release push [path]`
Crea el Package si no existe y sube el zip como nueva Release. **Requiere rol
admin** — verifica antes y avisa al usuario si su rol no alcanza.
También: `nora release list|delete <ver>|download <ver>`, flags `--package`,
`--file`, `--no-create`.

## Pipeline completo de despliegue

```bash
# 1. Validar y probar (ver testing-and-validation.md)
python3 <skill>/scripts/validate_manifest.py .
python -m pytest tests/ -q
python main.py
nora dev run main.py --input '{...}' -e dev

# 2. Publicar
nora package                        # → dist/mi-robot-1.0.1.zip
nora release push                   # → Release en NORA (rol admin)

# 3. Crear/actualizar el proceso (una vez; luego solo release push)
python3 <skill>/scripts/nora_process.py create \
  --name "Mi proceso" --release mi-robot@1.0.1 \
  --timeout 1800 --max-retries 2 --assets CRED1

# 4. Smoke e2e en una máquina real
python3 <skill>/scripts/nora_smoke.py --process "Mi proceso" \
  --input '{...}' --expect-output procesados=3
```

Notas:
- Un proceso existente sigue apuntando a su release: tras `release push`
  actualiza la release activa del proceso desde la consola (o recrea el
  proceso apuntando a la nueva).
- Programar: `nora_schedule.py create --process "Mi proceso" --cron "0 7 * * 1-5" --tz America/Lima --skip-holidays`.
- Disparo desde sistemas externos: `nora_trigger_mgmt.py create` (webhook con
  HMAC) o `POST /webhooks/trigger/{process_id}` con API key.

## CI/CD

Workflow listo: `templates/snippets/github-actions-deploy.yml`
(validate → pytest → package → release push con credenciales en secrets).
