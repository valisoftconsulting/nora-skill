"""Configuración del robot. Solo constantes — nada de lógica."""

# Cola de trabajo (créala antes: nora_queue.py create mi-cola-web)
QUEUE = "mi-cola-web"

# Asset con la URL del sistema (type=text) — así cambia por entorno sin tocar código.
URL_ASSET = "APP_URL"
URL_FALLBACK = "https://example.com"

# Asset credential con usuario/contraseña de la app (si aplica).
CRED_ASSET = "APP_CREDENCIALES"
