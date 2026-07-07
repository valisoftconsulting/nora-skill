#!/usr/bin/env python3
"""Cliente compartido de la API de NORA para los scripts del skill.

Solo stdlib (urllib). Doble autenticación:

1. **API key** (preferida): env var ``NORA_API_KEY`` (``nora_ak_...``) →
   endpoints públicos con header ``X-API-Key``. Contrato estable.
2. **Sesión del CLI** (fallback): si no hay API key, o la key no tiene el
   scope/endpoint, se usa la sesión de ``nora login``
   (``~/.nora/credentials.json``) contra los endpoints internos de la consola.
   El refresh token ROTA en cada uso — este cliente guarda el nuevo.

Env vars:
    NORA_API_URL   base de la API (default https://nora-api.valisoftconsulting.com/api/v1)
    NORA_API_KEY   API key pública (opcional si hay sesión de `nora login`)

Convenciones de los scripts que lo usan:
    stdout → SOLO JSON (parseable por agentes) · stderr → mensajes humanos
    exit 0 = OK · 1 = error de la operación/API · 2 = uso/credenciales
"""

from __future__ import annotations

import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_API_URL = "https://nora-api.valisoftconsulting.com/api/v1"
SESSION_FILE = Path.home() / ".nora" / "credentials.json"
USER_AGENT = "nora-skill/1.0"
MAX_RETRIES_429 = 3


class NoraError(Exception):
    """Error operativo: mensaje para stderr + exit code sugerido."""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


def api_url() -> str:
    url = os.environ.get("NORA_API_URL", DEFAULT_API_URL).rstrip("/")
    if url.startswith("http://") and not any(
        h in url for h in ("localhost", "127.0.0.1", "[::1]")
    ):
        raise NoraError("NORA_API_URL debe ser https (http solo para localhost).", 2)
    return url


def _api_key() -> str | None:
    key = os.environ.get("NORA_API_KEY", "").strip()
    return key or None


def seg(value: str) -> str:
    """Percent-encodea un segmento de path (nombres de colas/assets con
    espacios, '/', '?', '#'...). Igual criterio que _seg() del SDK."""
    return urllib.parse.quote(str(value), safe="")


def eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def emit(data) -> None:
    """Imprime el resultado como JSON en stdout (contrato con el agente)."""
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


# --- HTTP crudo -----------------------------------------------------------------

def _http(method: str, url: str, headers: dict, body: dict | None) -> dict:
    payload = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=payload, method=method)
    request.add_header("User-Agent", USER_AGENT)
    request.add_header("Accept", "application/json")
    if payload is not None:
        request.add_header("Content-Type", "application/json")
    for name, value in headers.items():
        request.add_header(name, value)

    context = ssl.create_default_context()
    attempt = 0
    while True:
        try:
            with urllib.request.urlopen(request, timeout=30, context=context) as resp:
                raw = resp.read().decode() or "{}"
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            raw = e.read().decode(errors="replace")
            if e.code == 429 and attempt < MAX_RETRIES_429:
                attempt += 1
                try:
                    wait = int(e.headers.get("Retry-After") or 0)
                except ValueError:
                    wait = 0
                wait = wait or (2 ** attempt * 5)
                eprint(f"[429] Rate limit — reintento {attempt}/{MAX_RETRIES_429} en {wait}s...")
                time.sleep(wait)
                continue
            try:
                detail = json.loads(raw)
            except json.JSONDecodeError:
                detail = {"detail": raw[:300]}
            message = (
                detail.get("message")
                or detail.get("detail")
                or (detail.get("error") or {}).get("message")
                or raw[:300]
            )
            raise NoraError(f"HTTP {e.code}: {message}", 1) from None
        except urllib.error.URLError as e:
            raise NoraError(f"No pude conectar con {url}: {e.reason}", 1) from None


def _unwrap(response: dict):
    """Desenvuelve {"success": true, "data": ...} (con meta si es paginado)."""
    if isinstance(response, dict) and "data" in response:
        if "meta" in response:
            return {"data": response["data"], "meta": response["meta"]}
        return response["data"]
    return response


# --- Sesión del CLI (~/.nora/credentials.json) ------------------------------------

_session_token_cache: str | None = None


class _SessionLock:
    """Lock de archivo entre procesos para el canje del refresh token.

    El backend ROTA el refresh en cada canje (detección de reuso): dos scripts
    en paralelo canjeando el mismo token pueden invalidar la sesión. Este lock
    serializa el canje. Best-effort multiplataforma (O_CREAT|O_EXCL + espera);
    un lock huérfano expira a los 30s.
    """

    LOCK = SESSION_FILE.with_suffix(".lock")

    def __enter__(self):
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                fd = os.open(self.LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                return self
            except FileExistsError:
                try:
                    if time.time() - self.LOCK.stat().st_mtime > 30:
                        self.LOCK.unlink(missing_ok=True)
                        continue
                except OSError:
                    pass
                time.sleep(0.2)
        return self  # timeout: seguir sin lock (mejor intentar que morir)

    def __exit__(self, *exc):
        try:
            self.LOCK.unlink(missing_ok=True)
        except OSError:
            pass


def _session_access_token() -> str | None:
    """Canjea el refresh token de `nora login` por un access token (y rota).

    Serializado con _SessionLock para no invalidar la sesión si dos scripts
    corren a la vez.
    """
    global _session_token_cache
    if _session_token_cache:
        return _session_token_cache
    if not SESSION_FILE.exists():
        return None
    with _SessionLock():
        return _session_refresh_locked()


def _session_refresh_locked() -> str | None:
    global _session_token_cache
    if _session_token_cache:
        return _session_token_cache
    try:
        session = json.loads(SESSION_FILE.read_text())
        base = (session.get("api_url") or api_url()).rstrip("/")
        refresh = session["refresh_token"]
    except (KeyError, ValueError):
        return None

    body = json.dumps({"refresh_token": refresh}).encode()
    request = urllib.request.Request(f"{base}/auth/refresh", data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    request.add_header("User-Agent", USER_AGENT)
    host = urllib.parse.urlparse(base).hostname or ""
    request.add_header("Cookie", f"nora_refresh_token={refresh}")
    try:
        with urllib.request.urlopen(request, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            new_refresh = refresh
            for header in resp.headers.get_all("Set-Cookie") or []:
                if "nora_refresh_token=" in header:
                    new_refresh = header.split("nora_refresh_token=")[1].split(";")[0]
            payload = data.get("data") or data
            token = payload.get("access_token")
    except (urllib.error.URLError, ValueError, KeyError):
        return None
    if not token:
        return None
    # El backend rota el refresh token: persistir el nuevo o la próxima falla.
    if new_refresh != refresh:
        SESSION_FILE.write_text(json.dumps({"api_url": base, "refresh_token": new_refresh}))
        os.chmod(SESSION_FILE, 0o600)
    _session_token_cache = token
    _ = host  # (solo informativo)
    return token


# --- Llamadas de alto nivel ---------------------------------------------------------

def call_api_key(method: str, path: str, body: dict | None = None, params: dict | None = None):
    key = _api_key()
    if not key:
        raise NoraError(
            "Falta NORA_API_KEY. Genera una en NORA → Settings → API Keys "
            "(planes Pro/Enterprise) y exporta: export NORA_API_KEY=nora_ak_...",
            2,
        )
    url = api_url() + path
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    return _unwrap(_http(method, url, {"X-API-Key": key}, body))


def call_session(method: str, path: str, body: dict | None = None, params: dict | None = None):
    token = _session_access_token()
    if not token:
        raise NoraError(
            "No hay sesión de `nora login`. Ejecuta `nora login` (pip install nora-sdk) "
            "o define NORA_API_KEY.",
            2,
        )
    url = api_url() + path
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    return _unwrap(_http(method, url, {"Authorization": f"Bearer {token}"}, body))


def call(
    method: str,
    path: str,
    body: dict | None = None,
    params: dict | None = None,
    session_path: str | None = None,
    session_method: str | None = None,
):
    """API key primero; si no hay key o le falta scope/feature (401/403),
    degrada a la sesión de `nora login` (endpoint interno equivalente)."""
    has_key = _api_key() is not None
    if has_key:
        try:
            return call_api_key(method, path, body, params)
        except NoraError as e:
            granted = str(e).startswith(("HTTP 401", "HTTP 403"))
            if not (granted and session_path):
                raise
            eprint(f"[aviso] API key sin acceso a {path} — usando sesión de `nora login`.")
    if session_path is None:
        return call_api_key(method, path, body, params)  # re-lanza el error de key ausente
    return call_session(session_method or method, session_path, body, params)


def run(main_fn) -> None:
    """Wrapper de entrada: mapea NoraError a exit codes y stderr limpio."""
    try:
        main_fn()
    except NoraError as e:
        eprint(f"Error: {e}")
        sys.exit(e.exit_code)
    except KeyboardInterrupt:
        eprint("Interrumpido.")
        sys.exit(130)
