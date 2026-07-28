// Vocabulario compartido entre dominios. Los textos de cada feature viven en
// su propio módulo (trips.ts, expenses.ts…): aquí solo lo transversal.
export default {
  actions: {
    save: 'Guardar',
    cancel: 'Cancelar',
    delete: 'Eliminar',
    add: 'Añadir',
    edit: 'Editar',
    close: 'Cerrar',
    search: 'Buscar',
    create: 'Crear',
    clear: 'Limpiar',
    retry: 'Reintentar',
    apply: 'Aplicar',
    filters: 'Filtros',
    changeColor: 'Cambiar color',
  },
  // navegación principal (AppNav)
  nav: {
    trips: 'Viajes',
    map: 'Mapa',
    packing: 'Maletas',
    travelers: 'Viajeros',
    settings: 'Ajustes',
  },
  // menú de usuario (AppNav, derecha)
  userMenu: {
    profile: 'Perfil',
    settings: 'Ajustes',
    logout: 'Cerrar sesión',
  },
  // selector de pagador (PayerSelect)
  payer: {
    unassigned: 'Sin asignar',
    anyPayer: 'Todos los pagadores',
    commonFund: 'Fondo común',
  },
  // adjuntos (AttachmentList)
  attachments: {
    attach: 'Adjuntar',
    uploadError: 'Error al subir',
    deleteHeader: 'Eliminar adjunto',
    deleteConfirm: '¿Eliminar el fichero "{name}"?',
  },
  // selector de rango de fechas (DateRangePicker)
  dateRange: {
    start: 'Inicio',
    end: 'Fin',
    pickDate: 'Elegir fecha',
    pickStart: 'Elige la fecha de inicio',
    pickEnd: 'Elige la fecha de fin',
  },
  // enlaces cruzados sitio/reserva/gasto (EntityLink)
  entityLink: {
    viewPlace: 'Ver sitio',
    viewBooking: 'Ver reserva',
    viewExpense: 'Ver gasto',
    viewAttachment: 'Ver adjunto',
  },
  // popups del mapa (PlaceMap)
  map: {
    visited: 'visitado',
    stopDays: 'sin fechas | {n} día | {n} días',
  },
  // diálogos de formulario (useFormDialog)
  form: {
    saveError: 'Error al guardar',
  },
  pageHeader: {
    infoAria: 'Información sobre {title}',
  },
  // labels de los enums de constants.ts (TRIP_STATUS_KEYS, etc.)
  tripStatus: {
    planning: 'Planificando',
    upcoming: 'Próximo',
    ongoing: 'En curso',
    done: 'Terminado',
  },
  placeCategory: {
    city: 'Ciudad',
    town: 'Pueblo',
    sight: 'Monumento',
    food: 'Comida',
    museum: 'Museo',
    nature: 'Naturaleza',
    viewpoint: 'Mirador',
    shopping: 'Compras',
    lodging: 'Alojamiento',
    other: 'Otro',
  },
  bookingType: {
    hotel: 'Hotel',
    flight: 'Vuelo',
    train: 'Tren',
    bus: 'Bus',
    ferry: 'Ferry',
    car_rental: 'Coche de alquiler',
    activity: 'Actividad',
    other: 'Otro',
  },
}
