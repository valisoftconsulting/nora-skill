"""Configuración del robot. Solo constantes — nada de lógica."""

# Cola de trabajo (créala antes: nora_queue.py create mi-cola)
QUEUE = "mi-cola"

# Asset text con la RUTA del ejecutable de la app en las máquinas
# (así cambia por máquina/entorno sin tocar código).
APP_PATH_ASSET = "APP_EXE_PATH"
APP_PATH_FALLBACK = r"C:\\Program Files\\MiApp\\miapp.exe"

# Título (regex) de la ventana principal de la app.
MAIN_WINDOW_TITLE = ".*MiApp.*"
