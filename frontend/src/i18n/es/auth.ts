export default {
  login: {
    title: 'Inicia sesión',
    subtitle: 'Tu cuaderno de viajes te espera.',
    username: 'Usuario',
    password: 'Contraseña',
    submit: 'Entrar',
    error: 'No se pudo iniciar sesión',
  },
  bootstrap: {
    title: 'Crea la cuenta de administrador',
    hint: 'Primer arranque: esta cuenta gestionará los usuarios y las familias de la instancia.',
    travelerName: 'Tu nombre de viajero',
    confirmPassword: 'Repite la contraseña',
    submit: 'Crear cuenta',
    error: 'No se pudo crear la cuenta',
  },
  // recuperación de contraseña: el enlace sale por los logs del servidor y lo
  // reparte el administrador (la app no manda correos)
  forgot: {
    link: '¿Has olvidado la contraseña?',
    title: 'Recuperar la contraseña',
    hint: 'Escribe tu usuario y se generará un enlace para cambiarla. Turtle Trips no envía correos: el enlace se escribe en los registros del servidor.',
    submit: 'Generar el enlace',
    error: 'No se pudo generar el enlace',
    back: 'Volver a iniciar sesión',
    sent: {
      title: 'Enlace en el servidor',
      body: 'Si esa cuenta existe, el enlace ya está en los registros del servidor. Pídeselo a quien administra la instancia y ábrelo antes de que caduque.',
      hasLink: 'Ya tengo el enlace',
    },
  },
  reset: {
    title: 'Elige una contraseña nueva',
    checking: 'Comprobando el enlace…',
    forUser: 'Vas a cambiar la contraseña de {username}.',
    submit: 'Guardar y entrar',
    done: 'Contraseña cambiada',
    error: 'No se pudo cambiar la contraseña',
    paste: {
      label: 'Enlace de recuperación',
      hint: 'Pega el enlace que te ha pasado quien administra la instancia.',
      submit: 'Continuar',
    },
    invalid: {
      title: 'Enlace no válido',
      body: 'El enlace no vale o ha caducado. Los enlaces son de un solo uso: si ya lo has usado, pide otro.',
      paste: 'Pegar otro enlace',
      retry: 'Pedir un enlace nuevo',
    },
  },
  password: {
    current: 'Contraseña actual',
    new: 'Contraseña nueva',
    confirm: 'Repite la contraseña nueva',
    tooShort: 'La contraseña debe tener al menos 8 caracteres',
    mismatch: 'Las contraseñas no coinciden',
    change: 'Cambiar contraseña',
    changed: 'Contraseña cambiada',
    changeError: 'No se pudo cambiar la contraseña',
  },
}
