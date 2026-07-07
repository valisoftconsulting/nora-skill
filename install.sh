#!/usr/bin/env bash
# Instalador del skill NORA para Claude Code, OpenAI Codex y Gemini CLI.
#
# Uso:
#   ./install.sh --claude [--project <dir>]   # symlink en ~/.claude/skills/nora (o <dir>/.claude/skills/nora)
#   ./install.sh --codex  [--project <dir>]   # bloque puntero en ~/.codex/AGENTS.md (o <dir>/AGENTS.md)
#   ./install.sh --gemini [--project <dir>]   # bloque puntero en ~/.gemini/GEMINI.md (o <dir>/GEMINI.md)
#   ./install.sh --all    [--project <dir>]
#   ./install.sh --uninstall [--project <dir>]
#
# El repo clonado es la única fuente de verdad: `git pull` actualiza el skill.
# No muevas la carpeta después de instalar (symlink/punteros usan ruta absoluta).

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MARK_START="<!-- nora-skill:start -->"
MARK_END="<!-- nora-skill:end -->"

DO_CLAUDE=0; DO_CODEX=0; DO_GEMINI=0; DO_UNINSTALL=0; PROJECT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --claude) DO_CLAUDE=1 ;;
    --codex) DO_CODEX=1 ;;
    --gemini) DO_GEMINI=1 ;;
    --all) DO_CLAUDE=1; DO_CODEX=1; DO_GEMINI=1 ;;
    --uninstall) DO_UNINSTALL=1 ;;
    --project) PROJECT="$2"; shift ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Opción desconocida: $1 (usa --help)" >&2; exit 2 ;;
  esac
  shift
done

if [[ $DO_CLAUDE$DO_CODEX$DO_GEMINI == "000" && $DO_UNINSTALL == 0 ]]; then
  echo "Indica al menos un agente: --claude | --codex | --gemini | --all (o --uninstall)" >&2
  exit 2
fi

pointer_block() {
  cat <<EOF
$MARK_START
## Skill NORA (robots RPA de Valisoft)

Cuando el trabajo involucre NORA (robots Python, nora.json, colas, assets,
jobs, migraciones desde UiPath/Automation Anywhere, o la API del orquestador),
lee $SKILL_DIR/SKILL.md y sigue su selector de flujos A-D, cargando las
references solo bajo demanda. Reglas mínimas: cero credenciales hardcodeadas
(usa assets), valida con \`nora dev run\` antes de publicar, y clasifica
errores en business (terminal) vs system (reintenta).
$MARK_END
EOF
}

remove_block() { # $1 = archivo
  [[ -f "$1" ]] || return 0
  python3 - "$1" "$MARK_START" "$MARK_END" <<'PY'
import sys, re, pathlib
path, start, end = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
text = path.read_text()
new = re.sub(re.escape(start) + r".*?" + re.escape(end) + r"\n?", "", text, flags=re.S)
if new != text:
    path.write_text(new.rstrip() + "\n" if new.strip() else "")
    print(f"  · bloque removido de {path}")
PY
}

add_block() { # $1 = archivo
  mkdir -p "$(dirname "$1")"
  remove_block "$1"                    # idempotente: reemplaza si ya estaba
  { [[ -s "$1" ]] && cat "$1"; printf '\n'; pointer_block; } > "$1.tmp" && mv "$1.tmp" "$1"
  echo "  ✓ puntero instalado en $1"
}

claude_target() {
  if [[ -n "$PROJECT" ]]; then echo "$PROJECT/.claude/skills/nora"; else echo "$HOME/.claude/skills/nora"; fi
}
codex_target() {
  if [[ -n "$PROJECT" ]]; then echo "$PROJECT/AGENTS.md"; else echo "$HOME/.codex/AGENTS.md"; fi
}
gemini_target() {
  if [[ -n "$PROJECT" ]]; then echo "$PROJECT/GEMINI.md"; else echo "$HOME/.gemini/GEMINI.md"; fi
}

if [[ $DO_UNINSTALL == 1 ]]; then
  target="$(claude_target)"
  [[ -L "$target" ]] && rm "$target" && echo "  · symlink removido: $target"
  remove_block "$(codex_target)"
  remove_block "$(gemini_target)"
  echo "Desinstalado."
  exit 0
fi

if [[ $DO_CLAUDE == 1 ]]; then
  target="$(claude_target)"
  mkdir -p "$(dirname "$target")"
  [[ -L "$target" || -e "$target" ]] && rm -rf "$target"
  ln -s "$SKILL_DIR" "$target"
  echo "  ✓ Claude Code: $target → $SKILL_DIR"
fi

[[ $DO_CODEX == 1 ]] && add_block "$(codex_target)"
[[ $DO_GEMINI == 1 ]] && add_block "$(gemini_target)"

echo "Listo. Actualiza el skill con: git -C $SKILL_DIR pull"
