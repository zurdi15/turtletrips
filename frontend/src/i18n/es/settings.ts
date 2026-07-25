export default {
  title: 'Ajustes',
  language: {
    title: 'Idioma',
    hint: 'Idioma de la interfaz.',
  },
  appearance: {
    title: 'Apariencia',
    hint: 'Tema de la interfaz.',
    light: 'Claro',
    dark: 'Oscuro',
  },
  categories: {
    expense: {
      title: 'Categorías de gastos',
      hint: 'Renombrar una categoría actualiza también los gastos existentes.',
    },
    packing: {
      title: 'Categorías de maleta',
      hint: 'Se usan para agrupar los elementos de las maletas y plantillas.',
    },
    newPlaceholder: 'Nueva categoría…',
    confirmDelete: {
      message: '¿Eliminar la categoría "{name}"? Los elementos existentes conservan el nombre.',
      header: 'Eliminar categoría',
    },
    toast: {
      colorError: 'Error al cambiar el color',
      addError: 'Error al añadir',
      renameError: 'Error al renombrar',
    },
  },
  backup: {
    title: 'Copia de seguridad',
    hint: 'La copia incluye la base de datos completa y todos los adjuntos.',
    download: 'Descargar copia',
    restore: 'Restaurar desde copia…',
    confirm: {
      message:
        'Esto reemplazará TODOS los datos actuales (viajes, gastos, adjuntos…) ' +
        'por los de la copia. Esta acción no se puede deshacer.',
      header: 'Restaurar copia de seguridad',
      accept: 'Restaurar',
    },
    toast: {
      restored: 'Copia restaurada ({n} viajes)',
      restoreError: 'No se pudo restaurar',
    },
  },
}
