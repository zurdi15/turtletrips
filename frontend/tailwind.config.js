/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      // Utilidades semánticas respaldadas por los tokens --tt-* de style.css.
      // El modo oscuro entra solo redefiniendo las variables bajo html.tt-dark,
      // así que estas clases son dark-correctas sin variantes dark:.
      // Ojo: son colores completos → los modificadores de opacidad (/50) no aplican.
      colors: {
        // el primary de PrimeVue (emerald de Aura), para acentos interactivos
        primary: 'var(--p-primary-color)',
        page: 'var(--tt-page-bg)',
        surface: {
          DEFAULT: 'var(--tt-surface)',
          soft: 'var(--tt-surface-soft)',
          muted: 'var(--tt-surface-muted)',
          strong: 'var(--tt-surface-strong)',
          hover: 'var(--tt-surface-hover)',
        },
        line: {
          DEFAULT: 'var(--tt-line)',
          subtle: 'var(--tt-line-subtle)',
          faint: 'var(--tt-line-faint)',
          strong: 'var(--tt-line-strong)',
        },
        ink: {
          DEFAULT: 'var(--tt-ink)',
          strong: 'var(--tt-ink-strong)',
          heading: 'var(--tt-ink-heading)',
          secondary: 'var(--tt-ink-secondary)',
          muted: 'var(--tt-ink-muted)',
          faint: 'var(--tt-ink-faint)',
          disabled: 'var(--tt-ink-disabled)',
        },
        brand: {
          DEFAULT: 'var(--tt-brand)',
          strong: 'var(--tt-brand-strong)',
          tint: 'var(--tt-brand-tint)',
          'tint-strong': 'var(--tt-brand-tint-strong)',
        },
        info: {
          DEFAULT: 'var(--tt-info)',
          strong: 'var(--tt-info-strong)',
          tint: 'var(--tt-info-tint)',
          'tint-strong': 'var(--tt-info-tint-strong)',
          edge: 'var(--tt-info-edge)',
        },
        lodging: {
          DEFAULT: 'var(--tt-lodging)',
          strong: 'var(--tt-lodging-strong)',
          tint: 'var(--tt-lodging-tint)',
          'tint-strong': 'var(--tt-lodging-tint-strong)',
        },
        warn: {
          DEFAULT: 'var(--tt-warn)',
          strong: 'var(--tt-warn-strong)',
          tint: 'var(--tt-warn-tint)',
          'tint-strong': 'var(--tt-warn-tint-strong)',
        },
        nature: {
          strong: 'var(--tt-nature-strong)',
          tint: 'var(--tt-nature-tint)',
          'tint-hover': 'var(--tt-nature-tint-hover)',
        },
        'media-ph-start': 'var(--tt-media-ph-start)',
        'media-ph-end': 'var(--tt-media-ph-end)',
      },
      // strings a propósito (sin line-height): equivalen a los text-[11px]/[10px]
      // arbitrarios a los que sustituyen
      fontSize: {
        '2xs': '0.6875rem',
        '3xs': '0.625rem',
      },
      borderRadius: {
        card: 'var(--tt-radius-card)',
      },
      boxShadow: {
        lift: 'var(--tt-shadow-lift)',
        marker: 'var(--tt-shadow-marker)',
      },
      transitionTimingFunction: {
        spring: 'var(--tt-ease-spring)',
        bounce: 'var(--tt-ease-bounce)',
      },
      minWidth: {
        menu: '9rem',
      },
      maxWidth: {
        // nota de un gasto dentro de su celda: recortada a una línea o
        // desplegada, siempre en la misma columna estrecha
        note: '16rem',
      },
      // bandas de apilamiento: contenido 0-40 < paneles Leaflet 400-700
      // (aislados por .leaflet-container { z-index: 0 }) < overlays de mapa 500
      // < overlays de PrimeVue ~1100 < lightbox 1200
      zIndex: {
        header: '40',
        'map-overlay': '500',
        lightbox: '1200',
      },
    },
  },
  plugins: [],
}
