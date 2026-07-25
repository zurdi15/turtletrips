#!/usr/bin/env bash
# Guardas del sistema de tokens: fallan si vuelve a colarse un valor hardcoded.
# Uso: npm run guard:tokens (desde frontend/)
set -u
cd "$(dirname "$0")/.." || exit 1
fail=0

check() {
  local desc="$1"; shift
  local out
  out=$(rg -n "$@" 2>/dev/null)
  if [ -n "$out" ]; then
    echo "✗ $desc:"
    echo "$out" | head -20
    fail=1
  else
    echo "✓ $desc"
  fi
}

# hex fuera de theme.ts (excepciones: --tt-surface-soft en style.css, logo svg)
check "sin hex fuera de theme.ts" '^(?!.*--tt-surface-soft).*#[0-9a-fA-F]{3,8}\b' src -P \
  --glob '!**/theme.ts' --glob '!*.test.ts' --glob '!**/assets/**'

# la rampa slate solo puede aparecer en la allowlist (fondos sobre fotos)
check "sin utilidades slate-* (salvo allowlist sobre fotos)" \
  '(bg|text|border|ring|divide)-slate-[0-9]' src --glob '*.vue' --glob '*.ts' \
  --glob '!**/TripHeroCard.vue'

# tipografía/z-index/anchos arbitrarios ya tokenizados
check "sin text-[..px] ni z-[..] arbitrarios" 'text-\[[0-9]+px\]|z-\[[0-9]+\]|min-w-\[9rem\]' src

# el easing vive en el token --tt-ease-spring (única definición en style.css)
check "cubic-bezier solo en la definición del token" 'cubic-bezier' src --glob '!style.css'

# toasts/confirms solo a través de los composables (con paréntesis: la llamada,
# no las claves i18n tipo "toast.addError")
check "sin confirm.require/toast.add/String(err) fuera de composables" \
  'confirm\.require\(|toast\.add\(|String\(err\)' src --glob '!**/composables/**'

if [ "$fail" -eq 0 ]; then
  echo "Tokens OK"
else
  exit 1
fi
